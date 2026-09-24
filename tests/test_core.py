import os

import pytest

from app.kernel.money import from_db, to_db
from wsgi import create_app


@pytest.fixture
def client(tmp_path):
    os.environ['DATABASE_PATH']=str(tmp_path/'test.sqlite3')
    app=create_app({'TESTING':True,'SECRET_KEY':'test'}); return app.test_client()

def setup(client):
    return client.post('/api/setup/complete',json={'name':'Demo','legal_form':'sole','business_type':'ecommerce','currency':'SAR','admin_email':'admin@example.com','admin_password':'ChangeMe123!','admin_name':'Admin'})

def login(client):
    setup(client); return client.post('/api/auth/login',json={'email':'admin@example.com','password':'ChangeMe123!'})

def test_health(client): assert client.get('/api/health').json['status']=='ok'
def test_money_scale(): assert to_db('12.3456')==123456 and str(from_db(123456))=='12.3456'
def test_setup_and_permissions(client):
    assert setup(client).status_code==200
    assert client.get('/api/partners').status_code==401
    login(client); assert client.get('/api/partners').status_code==200

def test_audit_on_create(client):
    login(client); m=client.get('/api/auth/me').json; r=client.post('/api/partners',json={'name':'عميل','type':'company'},headers={'X-CSRF-Token':m['csrf_token']}); assert r.status_code==201
    assert client.get('/api/audit').status_code==200
