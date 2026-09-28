import pytest
from company_website import create_app
from company_website.models import User
from company_website.routes import _contains_blocked_email_syntax, _render_email_preview


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


def test_profile_redirects_when_not_logged_in(client):
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code == 302


def test_employees_redirects_when_not_logged_in(client):
    response = client.get('/employees', follow_redirects=False)
    assert response.status_code == 302


def test_healthz_endpoint(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['db'] == 'connected'


def test_email_preview_supports_profile_variables(app):
    user = User(
        '1', 'sample', '', first_name='Ada', last_name='Lovelace',
        email='ada@example.com', role='Engineer'
    )

    with app.app_context():
        preview = _render_email_preview(
            'Hello {{ firstname }} {{ lastname }} ({{ email }}, {{ role }}) - {{ company }}',
            user,
        )

    assert preview == 'Hello Ada Lovelace (ada@example.com, Engineer) - Placeholder Industries'


@pytest.mark.parametrize('token', ['[]', "''", '()', 'dict', 'request'])
def test_email_preview_filter_blocks_listed_tokens(token):
    assert _contains_blocked_email_syntax(f'{{{{ value {token} }}}}')
