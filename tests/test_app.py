import pytest
from company_website import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200


def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200


def test_about_page(client):
    response = client.get('/about')
    assert response.status_code == 200


def test_dashboard_redirects_when_not_logged_in(client):
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302


def test_healthz_endpoint(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['db'] == 'connected'
