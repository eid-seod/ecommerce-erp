import os

import pytest

from app.kernel.accounting_core import (
    PostedEntryImmutableError,
    delete_entry,
    post_entry,
    update_entry,
)
from app.kernel.money import from_db, to_db
from wsgi import create_app


@pytest.fixture
def client(tmp_path):
    os.environ['DATABASE_PATH']=str(tmp_path/'test.sqlite3')
    app=create_app({'TESTING':True,'SECRET_KEY':'test'}); return app.test_client()

def setup(client):
    return client.post('/api/auth/signup',json={'name':'Admin','email':'admin@example.com','password':'ChangeMe123!','company_name':'Demo','currency':'SAR'})

def login(client):
    setup(client); return client.post('/api/auth/login',json={'email':'admin@example.com','password':'ChangeMe123!'})

def test_health(client): assert client.get('/api/health').json['status']=='ok'
def test_money_scale(): assert to_db('12.3456')==123456 and str(from_db(123456))=='12.3456'
def test_setup_and_permissions(client):
    assert setup(client).status_code==201
    csrf=client.get('/api/auth/me').json['csrf_token']
    client.post('/api/auth/logout',headers={'X-CSRF-Token':csrf})
    assert client.get('/api/partners').status_code==401
    login(client); assert client.get('/api/partners').status_code==200


def test_chart_of_accounts_loads(client):
    login(client)
    response = client.get('/api/accounts')
    assert response.status_code == 200
    assert [item['code'] for item in response.json['items']] == ['5000', '4000', '3000', '2000', '1100', '1000']


def test_business_modules_load(client):
    login(client)
    assert client.get('/api/modules/overview').status_code == 200
    for resource in ['sales_orders', 'inventory_moves', 'purchase_orders', 'employees']:
        assert client.get(f'/api/{resource}').status_code == 200


def test_account_and_invoice_operations(client):
    login(client)
    csrf=client.get('/api/auth/me').json['csrf_token']
    account=client.post('/api/accounts',json={'code':'6100','name':'Other income','kind':'income'},headers={'X-CSRF-Token':csrf})
    assert account.status_code==201
    duplicate=client.post('/api/accounts',json={'code':'6100','name':'Duplicate','kind':'income'},headers={'X-CSRF-Token':csrf})
    assert duplicate.status_code==400 and duplicate.is_json
    invoice=client.post('/api/invoices',json={'description':'Demo service','quantity':'2','unit_price':'100','tax_rate':'15'},headers={'X-CSRF-Token':csrf})
    assert invoice.status_code==201
    invoice_id=invoice.json['id']
    posted=client.post(f'/api/invoices/{invoice_id}/post',headers={'X-CSRF-Token':csrf})
    assert posted.status_code==200
    assert client.get('/api/invoices').json['items'][0]['status']=='posted'


def test_manual_entry_rejects_unbalanced_and_is_immutable(client):
    login(client)
    csrf=client.get('/api/auth/me').json['csrf_token']
    account_ids=[item['id'] for item in client.get('/api/accounts').json['items'][:2]]
    with pytest.raises(ValueError):
        post_entry([{'account':account_ids[0],'debit':'100','credit':'0'},{'account':account_ids[1],'debit':'0','credit':'90'}], 1, 1)
    response=client.post('/api/accounting/manual-entry',json={'lines':[{'account':account_ids[0],'debit':'100','credit':'0'},{'account':account_ids[1],'debit':'0','credit':'90'}]},headers={'X-CSRF-Token':csrf})
    assert response.status_code==400
    posted=client.post('/api/accounting/manual-entry',json={'lines':[{'account':account_ids[0],'debit':'100','credit':'0'},{'account':account_ids[1],'debit':'0','credit':'100'}]},headers={'X-CSRF-Token':csrf})
    assert posted.status_code==201
    with client.application.app_context():
        with pytest.raises(PostedEntryImmutableError):
            update_entry(posted.json['id'], client.get('/api/auth/me').json['user']['company_id'], {})
        with pytest.raises(PostedEntryImmutableError):
            delete_entry(posted.json['id'], client.get('/api/auth/me').json['user']['company_id'])


def test_trial_balance_sums_posted_manual_entries(client):
    login(client)
    csrf=client.get('/api/auth/me').json['csrf_token']
    accounts=client.get('/api/accounts').json['items']
    cash=next(x['id'] for x in accounts if x['code']=='1000')
    bank=next(x['id'] for x in accounts if x['code']=='1100')
    for amount in ('100','200','300'):
        response=client.post('/api/accounting/manual-entry',json={'lines':[{'account':cash,'debit':amount,'credit':'0'},{'account':bank,'debit':'0','credit':amount}]},headers={'X-CSRF-Token':csrf})
        assert response.status_code==201
    trial={x['code']:x for x in client.get('/api/accounting/trial-balance').json['items']}
    assert trial['1000']['debit']==6000000
    assert trial['1100']['credit']==6000000


def test_company_data_is_isolated(tmp_path):
    os.environ['DATABASE_PATH']=str(tmp_path/'isolated.sqlite3')
    app=create_app({'TESTING':True,'SECRET_KEY':'test'})
    first=app.test_client(); second=app.test_client()
    assert first.post('/api/auth/signup',json={'name':'One','email':'one@example.com','password':'ChangeMe123!','company_name':'Company One'}).status_code==201
    csrf=first.get('/api/auth/me').json['csrf_token']
    assert first.post('/api/partners',json={'name':'Private customer'},headers={'X-CSRF-Token':csrf}).status_code==201
    assert second.post('/api/auth/signup',json={'name':'Two','email':'two@example.com','password':'ChangeMe123!','company_name':'Company Two'}).status_code==201
    assert second.get('/api/partners').json['items']==[]


def test_audit_on_create(client):
    login(client); m=client.get('/api/auth/me').json; r=client.post('/api/partners',json={'name':'عميل','type':'company'},headers={'X-CSRF-Token':m['csrf_token']}); assert r.status_code==201
    assert client.get('/api/audit').status_code==200
