import json
import sqlite3
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


def test_draft_saved_for_review(tmp_path, monkeypatch):
    monkeypatch.setenv('GBE_LOCAL_MODEL', 'local-test')
    def respond(request):
        body=json.loads(request.content)
        assert str(request.url)=='http://127.0.0.1:11434/api/chat'
        assert body['stream'] is False
        assert 'tools' not in body
        return httpx.Response(200,json={'done':True,'message':{'content':'Draft a test plan.'}})
    path=tmp_path/'db'
    with TestClient(create_app(path, httpx.MockTransport(respond))) as client:
        r=client.post('/api/agent/draft',json={'action':'diagnose','text':'Help plan testing'})
        assert r.status_code==200
        assert r.json()['status']=='needs_review'
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT action,result FROM requests').fetchone()==('offline_draft','Draft a test plan.')

@pytest.mark.parametrize('mode, expected', [('missing',503),('cloud',400),('connection',503),('timeout',504),('not_found',503),('invalid',502)])
def test_model_failures(tmp_path,monkeypatch,mode,expected):
    monkeypatch.setenv('GBE_LOCAL_MODEL', '' if mode=='missing' else 'test-cloud' if mode=='cloud' else 'local-test')
    def respond(request):
        if mode in ('missing','cloud'): pytest.fail('Model must not be called')
        if mode=='connection': raise httpx.ConnectError('offline')
        if mode=='timeout': raise httpx.ReadTimeout('slow')
        if mode=='not_found': return httpx.Response(404)
        return httpx.Response(200,json={'done':False,'message':{}})
    path=tmp_path/'db'
    with TestClient(create_app(path,httpx.MockTransport(respond))) as client:
        r=client.post('/api/agent/draft',json={'action':'diagnose','text':'Draft a plan'})
        assert r.status_code==expected
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT count(*) FROM requests').fetchone()[0]==0
