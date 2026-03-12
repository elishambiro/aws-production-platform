import requests

BASE_URL = "http://localhost:5000"


def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data


def test_metrics_endpoint():
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    assert b'http_requests_total' in response.content


def test_create_item():
    payload = {"name": "test-item", "value": "test-value"}
    response = requests.post(f"{BASE_URL}/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert 'id' in data
    assert 'timestamp' in data
    assert data['name'] == 'test-item'


def test_get_items():
    response = requests.get(f"{BASE_URL}/items")
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'count' in data
    assert isinstance(data['items'], list)


def test_create_and_verify_item():
    payload = {"name": "verify-test", "value": "123"}
    create_response = requests.post(f"{BASE_URL}/items", json=payload)
    assert create_response.status_code == 201

    get_response = requests.get(f"{BASE_URL}/items")
    assert get_response.status_code == 200
    items = get_response.json()['items']
    names = [item.get('name') for item in items]
    assert 'verify-test' in names
