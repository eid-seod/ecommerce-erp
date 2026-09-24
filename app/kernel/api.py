"""JSON API with signup, company tenancy, authentication, and module CRUD."""
import re
import secrets
from decimal import Decimal

from flask import Blueprint, jsonify, request, session

from .accounting import post_journal
from .audit import log
from .db import get_db, transaction
from .money import to_db
from .security import (
    csrf_token,
    current_user,
    hash_password,
    permission,
    require_csrf,
    verify_password,
)


def rows(sql, args=()):
    return [dict(r) for r in get_db().execute(sql, args).fetchall()]


def json_body():
    return request.get_json(silent=True) or {}


def company_id():
    user = current_user()
    return user['company_id'] if user else None


def slugify(value):
    slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-') or 'company'
    return slug + '-' + secrets.token_hex(3)


def register():
    api = Blueprint('api', __name__, url_prefix='/api')

    @api.before_request
    def csrf():
        return require_csrf()

    @api.get('/health')
    def health():
        return jsonify(status='ok')

    @api.get('/auth/me')
    def me():
        user = current_user()
        company = None
        if user and user['company_id']:
            company = get_db().execute('SELECT id,name,slug,currency FROM companies WHERE id=?', (user['company_id'],)).fetchone()
        return jsonify(authenticated=bool(user), user=dict(user) if user else None, company=dict(company) if company else None, csrf_token=csrf_token())

    @api.post('/auth/signup')
    def signup():
        data = json_body()
        required = ['name', 'email', 'password', 'company_name']
        missing = [key for key in required if not data.get(key)]
        if missing:
            return jsonify(error='Missing fields', fields=missing), 400
        email = data['email'].strip().lower()
        with transaction() as db:
            if db.execute('SELECT 1 FROM users WHERE email=?', (email,)).fetchone():
                return jsonify(error='البريد الإلكتروني مستخدم بالفعل'), 409
            cur = db.execute('INSERT INTO companies(name,slug,currency) VALUES (?,?,?)', (data['company_name'].strip(), slugify(data['company_name']), data.get('currency', 'SAR')))
            cid = cur.lastrowid
            role = db.execute("SELECT id FROM roles WHERE name='Admin'").fetchone()
            if not role:
                db.execute("INSERT INTO roles(name) VALUES ('Admin')")
                role = db.execute('SELECT last_insert_rowid() id').fetchone()
            perms = ['base.user.view','base.user.create','base.role.manage','base.settings.manage','contacts.partner.view','contacts.partner.create','accounting.journal.post','accounting.report.view','accounting.account.create','sales.order.view','sales.order.create','sales.invoice.view','sales.invoice.create','sales.invoice.post','inventory.move.view','inventory.move.create','purchase.order.view','purchase.order.create','hr.employee.view','hr.employee.create']
            for code in perms:
                db.execute('INSERT OR IGNORE INTO role_permissions(role_id,permission) VALUES (?,?)', (role['id'], code))
            cur = db.execute('INSERT INTO users(email,password_hash,name,company_id) VALUES (?,?,?,?)', (email, hash_password(data['password']), data['name'].strip(), cid))
            uid = cur.lastrowid
            db.execute('INSERT INTO user_roles(user_id,role_id) VALUES (?,?)', (uid, role['id']))
            for code, name, kind in [('1000','Cash','asset'),('1100','Receivables','asset'),('2000','Payables','liability'),('3000','Capital','equity'),('4000','Sales revenue','income'),('5000','Cost of sales','expense')]:
                account_code = code if not db.execute('SELECT 1 FROM accounts WHERE code=?', (code,)).fetchone() else f'{code}-{cid}'
                db.execute('INSERT INTO accounts(code,name,kind,company_id) VALUES (?,?,?,?)', (account_code, name, kind, cid))
            db.execute("INSERT INTO fiscal_periods(name,start_date,end_date,status,company_id) VALUES (?,?,?,?,?)", ('FY 2026','2026-01-01','2026-12-31','open',cid))
        session.clear()
        session['user_id'] = uid
        csrf_token()
        return jsonify(ok=True, company_id=cid), 201

    @api.post('/auth/login')
    def login():
        data = json_body()
        user = get_db().execute('SELECT * FROM users WHERE email=? AND active=1', (data.get('email', '').lower(),)).fetchone()
        if not user or not verify_password(user['password_hash'], data.get('password', '')):
            return jsonify(error='بيانات الدخول غير صحيحة'), 401
        session.clear()
        session['user_id'] = user['id']
        csrf_token()
        return jsonify(user=dict(user))

    @api.post('/auth/logout')
    def logout():
        session.clear()
        return jsonify(ok=True)

    @api.get('/setup/status')
    def setup_status():
        return jsonify(configured=bool(get_db().execute('SELECT 1 FROM companies LIMIT 1').fetchone()))

    @api.get('/dashboard')
    @permission('accounting.report.view')
    def dashboard():
        cid = company_id()
        db = get_db()
        counts = {key: db.execute(f'SELECT COUNT(*) c FROM {table} WHERE company_id=?', (cid,)).fetchone()['c'] for key, table in [('partners','partners'),('products','products'),('journals','journals'),('accounts','accounts')]}
        company = db.execute('SELECT * FROM companies WHERE id=?', (cid,)).fetchone()
        return jsonify(company=dict(company or {}), counts=counts)

    @api.get('/modules/overview')
    @permission('accounting.report.view')
    def modules_overview():
        cid = company_id()
        db = get_db()
        tables = {'sales':'sales_orders','inventory':'inventory_moves','purchase':'purchase_orders','hr':'employees'}
        return jsonify(modules={key: db.execute(f'SELECT COUNT(*) c FROM {table} WHERE company_id=? AND active=1', (cid,)).fetchone()['c'] for key, table in tables.items()})

    resources = {
        'partners': ('partners','contacts.partner.view','contacts.partner.create',['name','type','tax_id','phone','email']),
        'products': ('products','accounting.report.view','catalog.product.create',['name','sku','product_type','sale_price']),
        'accounts': ('accounts','accounting.report.view','accounting.account.create',['code','name','kind']),
        'sales_orders': ('sales_orders','sales.order.view','sales.order.create',['number','partner_id','order_date','status','total']),
        'inventory_moves': ('inventory_moves','inventory.move.view','inventory.move.create',['reference','product_id','quantity','direction','warehouse','status','source']),
        'purchase_orders': ('purchase_orders','purchase.order.view','purchase.order.create',['number','partner_id','order_date','status','total']),
        'employees': ('employees','hr.employee.view','hr.employee.create',['employee_code','name','department','job_title','email','hire_date','status']),
    }
    for endpoint, (table, view_perm, create_perm, fields) in resources.items():
        def list_resource(table=table, view_perm=view_perm, fields=fields):
            @permission(view_perm)
            def inner():
                selected = ','.join(fields)
                return jsonify(items=rows(f'SELECT id,{selected},active,version FROM {table} WHERE company_id=? AND active=1 ORDER BY id DESC LIMIT 200', (company_id(),)))
            return inner()
        api.add_url_rule('/' + endpoint, endpoint + '_list', list_resource, methods=['GET'])

        def create_resource(table=table, create_perm=create_perm, fields=fields):
            @permission(create_perm)
            def inner():
                data = json_body()
                cols = [field for field in fields if field in data]
                if not cols:
                    return jsonify(error='No fields supplied'), 400
                values = [data[field] for field in cols]
                cols.append('company_id')
                values.append(company_id())
                with transaction() as db:
                    cur = db.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", values)
                    log('create', table, cur.lastrowid, new_value=str(data), user_id=current_user()['id'])
                return jsonify(id=cur.lastrowid), 201
            return inner()
        api.add_url_rule('/' + endpoint, endpoint + '_create', create_resource, methods=['POST'])

    @api.get('/invoices')
    @permission('sales.invoice.view')
    def invoices():
        items = rows('SELECT id,number,partner_id,invoice_date,status,subtotal,tax_total,total,currency,version FROM invoices WHERE company_id=? AND active=1 ORDER BY id DESC LIMIT 200', (company_id(),))
        for item in items:
            item['lines'] = rows('SELECT id,description,quantity,unit_price,tax_rate,line_total FROM invoice_lines WHERE invoice_id=? ORDER BY id', (item['id'],))
        return jsonify(items=items)

    @api.post('/invoices')
    @permission('sales.invoice.create')
    def create_invoice():
        data = json_body()
        lines = data.get('lines') or [{'description': data.get('description'), 'quantity': data.get('quantity', '1'), 'unit_price': data.get('unit_price', '0'), 'tax_rate': data.get('tax_rate', '0')}]
        if not lines or any(not line.get('description') for line in lines):
            return jsonify(error='يجب إدخال وصف لكل سطر'), 400
        subtotal = Decimal(0)
        tax_total = Decimal(0)
        normalized = []
        for line in lines:
            quantity = Decimal(str(line.get('quantity', '1')))
            unit_price = Decimal(str(line.get('unit_price', '0')))
            tax_rate = Decimal(str(line.get('tax_rate', '0')))
            line_total = quantity * unit_price
            tax = line_total * tax_rate / Decimal(100)
            subtotal += line_total
            tax_total += tax
            normalized.append((line['description'], quantity, unit_price, tax_rate, line_total))
        with transaction() as db:
            number = f"INV-{company_id()}-{secrets.token_hex(4).upper()}"
            cur = db.execute('INSERT INTO invoices(number,partner_id,invoice_date,status,subtotal,tax_total,total,currency,company_id) VALUES (?,?,COALESCE(?,CURRENT_DATE),?,?,?,?,?,?)', (number, data.get('partner_id'), data.get('invoice_date'), 'draft', to_db(subtotal), to_db(tax_total), to_db(subtotal + tax_total), data.get('currency', 'SAR'), company_id()))
            invoice_id = cur.lastrowid
            for description, quantity, unit_price, tax_rate, line_total in normalized:
                db.execute('INSERT INTO invoice_lines(invoice_id,description,quantity,unit_price,tax_rate,line_total) VALUES (?,?,?,?,?,?)', (invoice_id, description, to_db(quantity), to_db(unit_price), to_db(tax_rate), to_db(line_total)))
            log('create', 'invoices', invoice_id, new_value=str(data), user_id=current_user()['id'])
        return jsonify(id=invoice_id, number=number, subtotal=to_db(subtotal), tax_total=to_db(tax_total), total=to_db(subtotal + tax_total)), 201

    @api.post('/invoices/<int:invoice_id>/post')
    @permission('sales.invoice.post')
    def post_invoice(invoice_id):
        with transaction() as db:
            invoice = db.execute('SELECT * FROM invoices WHERE id=? AND company_id=? AND status=\'draft\'', (invoice_id, company_id())).fetchone()
            if not invoice:
                return jsonify(error='الفاتورة غير موجودة أو تم ترحيلها'), 404
            period = db.execute('SELECT * FROM fiscal_periods WHERE company_id=? AND status=\'open\' ORDER BY id LIMIT 1', (company_id(),)).fetchone()
            receivable = db.execute("SELECT id FROM accounts WHERE company_id=? AND code LIKE '1100%' LIMIT 1", (company_id(),)).fetchone()
            revenue = db.execute("SELECT id FROM accounts WHERE company_id=? AND kind='income' LIMIT 1", (company_id(),)).fetchone()
            tax_account = db.execute("SELECT id FROM accounts WHERE company_id=? AND kind='liability' LIMIT 1", (company_id(),)).fetchone()
            if not period or not receivable or not revenue:
                return jsonify(error='الحسابات أو الفترة المحاسبية غير مكتملة'), 400
            cur = db.execute('INSERT INTO journals(reference,journal_date,period_id,memo,status,created_by,company_id) VALUES (?,?,?,? ,\'draft\',?,?)', (f'INV-J-{invoice_id}', invoice['invoice_date'], period['id'], f'فاتورة {invoice["number"]}', current_user()['id'], company_id()))
            journal_id = cur.lastrowid
            db.execute('INSERT INTO journal_lines(journal_id,account_id,partner_id,debit,credit,memo,source_type,source_id) VALUES (?,?,?,?,?,?,?,?)', (journal_id, receivable['id'], invoice['partner_id'], invoice['total'], 0, 'ذمم مدينة', 'invoice', invoice_id))
            db.execute('INSERT INTO journal_lines(journal_id,account_id,partner_id,debit,credit,memo,source_type,source_id) VALUES (?,?,?,?,?,?,?,?)', (journal_id, revenue['id'], invoice['partner_id'], 0, invoice['subtotal'], 'إيراد مبيعات', 'invoice', invoice_id))
            if invoice['tax_total'] and tax_account:
                db.execute('INSERT INTO journal_lines(journal_id,account_id,partner_id,debit,credit,memo,source_type,source_id) VALUES (?,?,?,?,?,?,?,?)', (journal_id, tax_account['id'], invoice['partner_id'], 0, invoice['tax_total'], 'ضريبة مخرجات', 'invoice', invoice_id))
        try:
            post_journal(journal_id, current_user()['id'])
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        with transaction() as db:
            db.execute("UPDATE invoices SET status='posted',journal_id=? WHERE id=? AND company_id=?", (journal_id, invoice_id, company_id()))
        return jsonify(ok=True, journal_id=journal_id)

    @api.get('/accounting/trial-balance')
    @permission('accounting.report.view')
    def trial_balance():
        return jsonify(items=rows("SELECT a.code,a.name,COALESCE(SUM(l.debit),0) debit,COALESCE(SUM(l.credit),0) credit FROM accounts a LEFT JOIN journal_lines l ON l.account_id=a.id LEFT JOIN journals j ON j.id=l.journal_id AND j.status='posted' WHERE a.company_id=? GROUP BY a.id ORDER BY a.code", (company_id(),)))

    @api.post('/accounting/journals/<int:jid>/post')
    @permission('accounting.journal.post')
    def post(jid):
        try:
            post_journal(jid, current_user()['id'])
            return jsonify(ok=True)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    @api.get('/audit')
    @permission('base.settings.manage')
    def audit():
        return jsonify(items=rows('SELECT * FROM audit_log ORDER BY id DESC LIMIT 200'))

    return api
