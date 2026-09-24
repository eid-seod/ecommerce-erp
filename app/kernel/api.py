"""JSON API routes for setup, auth, CRUD, and accounting."""
from flask import Blueprint, jsonify, request, session

from .accounting import post_journal
from .audit import log
from .db import get_db, transaction
from .security import (
    csrf_token,
    current_user,
    hash_password,
    permission,
    require_csrf,
    verify_password,
)


def rows(sql, args=()): return [dict(r) for r in get_db().execute(sql, args).fetchall()]
def json_body(): return request.get_json(silent=True) or {}

def register():
    api = Blueprint('api', __name__, url_prefix='/api')
    @api.before_request
    def csrf(): return require_csrf()
    @api.get('/health')
    def health(): return jsonify(status='ok')
    @api.get('/auth/me')
    def me():
        u=current_user(); return jsonify(authenticated=bool(u), user=dict(u) if u else None, csrf_token=csrf_token())
    @api.post('/auth/login')
    def login():
        data=json_body(); u=get_db().execute('SELECT * FROM users WHERE email=? AND active=1',(data.get('email','').lower(),)).fetchone()
        if not u or not verify_password(u['password_hash'], data.get('password','')): return jsonify(error='Invalid credentials'),401
        session.clear(); session['user_id']=u['id']; csrf_token(); return jsonify(user=dict(u))
    @api.post('/auth/logout')
    def logout(): session.clear(); return jsonify(ok=True)
    @api.get('/setup/status')
    def setup_status(): return jsonify(configured=bool(get_db().execute('SELECT 1 FROM company LIMIT 1').fetchone()))
    @api.post('/setup/complete')
    def setup_complete():
        d=json_body(); required=['name','legal_form','business_type','currency','admin_email','admin_password']
        missing=[x for x in required if not d.get(x)]
        if missing: return jsonify(error='Missing fields', fields=missing),400
        with transaction() as db:
            if db.execute('SELECT 1 FROM company LIMIT 1').fetchone(): return jsonify(error='Already configured'),409
            db.execute('INSERT INTO company(name, legal_form, business_type, currency, decimals) VALUES (?,?,?,?,?)',(d['name'],d['legal_form'],d['business_type'],d['currency'],int(d.get('decimals',2))))
            db.execute('INSERT INTO roles(name) VALUES (?)',('Admin',)); role=db.execute('SELECT last_insert_rowid() id').fetchone()['id']
            perms=['base.user.view','base.user.create','base.role.manage','base.settings.manage','contacts.partner.view','contacts.partner.create','accounting.journal.post','accounting.report.view']
            for p in perms: db.execute('INSERT INTO role_permissions(role_id,permission) VALUES (?,?)',(role,p))
            db.execute('INSERT INTO users(email,password_hash,name) VALUES (?,?,?)',(d['admin_email'].lower(),hash_password(d['admin_password']),d.get('admin_name','Administrator'))); uid=db.execute('SELECT last_insert_rowid() id').fetchone()['id']; db.execute('INSERT INTO user_roles(user_id,role_id) VALUES (?,?)',(uid,role))
            for code,name,kind in [('1000','Cash','asset'),('1100','Receivables','asset'),('2000','Payables','liability'),('3000','Capital','equity'),('4000','Sales revenue','income'),('5000','Cost of sales','expense')]: db.execute('INSERT INTO accounts(code,name,kind) VALUES (?,?,?)',(code,name,kind))
            db.execute('INSERT INTO fiscal_periods(name,start_date,end_date,status) VALUES (?,?,?,?)',('FY '+d.get('fiscal_year','2026'),d.get('fiscal_start','2026-01-01'),'2026-12-31','open'))
        return jsonify(ok=True)
    @api.get('/dashboard')
    @permission('accounting.report.view')
    def dashboard():
        db=get_db(); return jsonify(company=dict(db.execute('SELECT * FROM company LIMIT 1').fetchone() or {}), counts={k:db.execute(f'SELECT COUNT(*) c FROM {t}').fetchone()['c'] for k,t in [('partners','partners'),('products','products'),('journals','journals'),('accounts','accounts')]})
    resources={'partners':('partners','contacts.partner.view','contacts.partner.create',['name','type','tax_id','phone','email']), 'products':('products','catalog.product.view','catalog.product.create',['name','sku','product_type','sale_price']), 'accounts':('accounts','accounting.report.view','accounting.account.create',['code','name','kind'])}
    for endpoint,(table,view_perm,create_perm,fields) in resources.items():
        def list_resource(table=table, view_perm=view_perm, fields=fields):
            @permission(view_perm)
            def inner(): return jsonify(items=rows(f'SELECT id,{",".join(fields)},active,version FROM {table} WHERE active=1 ORDER BY id DESC LIMIT 200'))
            return inner()
        api.add_url_rule('/'+endpoint, endpoint+'_list', list_resource, methods=['GET'])
        def create_resource(table=table, create_perm=create_perm, fields=fields):
            @permission(create_perm)
            def inner():
                d=json_body(); cols=[f for f in fields if f in d];
                if not cols: return jsonify(error='No fields supplied'),400
                vals=[d[f] for f in cols]
                with transaction() as db:
                    cur=db.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", vals); log('create',table,cur.lastrowid,new_value=str(d),user_id=current_user()['id'])
                return jsonify(id=cur.lastrowid),201
            return inner()
        api.add_url_rule('/'+endpoint, endpoint+'_create', create_resource, methods=['POST'])
    @api.get('/accounting/trial-balance')
    @permission('accounting.report.view')
    def trial_balance():
        return jsonify(items=rows("SELECT a.code,a.name,COALESCE(SUM(l.debit),0) debit,COALESCE(SUM(l.credit),0) credit FROM accounts a LEFT JOIN journal_lines l ON l.account_id=a.id LEFT JOIN journals j ON j.id=l.journal_id AND j.status='posted' GROUP BY a.id ORDER BY a.code"))
    @api.post('/accounting/journals/<int:jid>/post')
    @permission('accounting.journal.post')
    def post(jid):
        try: post_journal(jid,current_user()['id']); return jsonify(ok=True)
        except ValueError as e: return jsonify(error=str(e)),400
    @api.get('/audit')
    @permission('base.settings.manage')
    def audit(): return jsonify(items=rows('SELECT * FROM audit_log ORDER BY id DESC LIMIT 200'))
    return api
