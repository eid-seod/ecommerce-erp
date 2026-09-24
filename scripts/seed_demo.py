"""Seed a safe demo company for local evaluation."""
import os

os.environ.setdefault('DATABASE_PATH','instance/erp.sqlite3')
from app.kernel.db import get_db
from app.kernel.security import hash_password
from wsgi import create_app

app=create_app()
with app.app_context():
 db=get_db()
 if not db.execute('SELECT 1 FROM company').fetchone():
  db.execute("INSERT INTO company(name,legal_form,business_type,currency) VALUES ('شركة نجد التجريبية','sole','ecommerce_manufacturing','SAR')")
  db.execute("INSERT INTO roles(name) VALUES ('Admin')"); role=db.execute('SELECT last_insert_rowid() id').fetchone()['id']
  for p in ['base.settings.manage','accounting.report.view','contacts.partner.view','contacts.partner.create','catalog.product.view','catalog.product.create','accounting.journal.post']: db.execute('INSERT INTO role_permissions VALUES (?,?)',(role,p))
  db.execute("INSERT INTO users(email,password_hash,name) VALUES ('admin@example.com',?,'مدير النظام')",(hash_password('ChangeMe123!'),)); uid=db.execute('SELECT last_insert_rowid() id').fetchone()['id']; db.execute('INSERT INTO user_roles VALUES (?,?)',(uid,role))
  for x in [('1000','النقدية','asset'),('1100','العملاء','asset'),('2000','الموردون','liability'),('3000','رأس المال','equity'),('4000','المبيعات','income'),('5000','تكلفة المبيعات','expense')]: db.execute('INSERT INTO accounts(code,name,kind) VALUES (?,?,?)',x)
  db.execute("INSERT INTO fiscal_periods(name,start_date,end_date) VALUES ('2026','2026-01-01','2026-12-31')")
  db.execute("INSERT INTO partners(name,type) VALUES ('عميل تجريبي','company')")
  db.execute("INSERT INTO products(name,sku,product_type,sale_price) VALUES ('منتج تجريبي','SKU-001','storable',1250000)")
  db.commit()
 print('Seeded demo: admin@example.com / ChangeMe123!')
