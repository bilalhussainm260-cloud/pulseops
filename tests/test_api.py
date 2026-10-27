import pytest
from fastapi.testclient import TestClient
from app import database
from app.main import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'test_orders.db')
    with TestClient(app) as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['database'] == 'connected'

def test_order_lifecycle(client):
    created = client.post('/orders', json={'item': 'coffee'})
    assert created.status_code == 201
    order_id = created.json()['id']
    assert client.get(f'/orders/{order_id}').json()['item'] == 'coffee'
    assert len(client.get('/orders').json()) == 1
    updated = client.put(f'/orders/{order_id}', json={'item': 'tea', 'status': 'completed'})
    assert updated.status_code == 200
    assert updated.json()['status'] == 'completed'
    assert client.delete(f'/orders/{order_id}').status_code == 200
    assert client.get(f'/orders/{order_id}').status_code == 404

def test_validation(client):
    assert client.post('/orders', json={'item': ''}).status_code == 422
    assert client.post('/orders', json={'item': 'tea', 'status': 'unknown'}).status_code == 422

def test_metrics(client):
    assert client.get('/metrics').status_code == 200
    assert 'uptime_seconds' in client.get('/metrics').json()
