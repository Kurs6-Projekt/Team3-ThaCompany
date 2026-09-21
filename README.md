# Company Website

A modular Flask application with Docker support.

## Local Development

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the environment file and run the app:

```bash
cp .env.example .env
python wsgi.py
```

Or with Flask CLI:

```bash
export PYTHONPATH=src
flask --app company_website run --port 7000
```

## Docker

Build and run with Docker Compose:

```bash
docker compose up --build
```

The SQLite database is persisted in a Docker volume (`app-data`).

For Kubernetes (k3s), replace the Docker volume with a PersistentVolumeClaim pointing to `/app/data`.

## Tests

Run tests with pytest:

```bash
pytest
```

## Project Structure

```
.
├── src/
│   └── company_website/
│       ├── __init__.py
│       ├── app.py          # Flask app factory
│       ├── config.py       # Configuration
│       ├── db.py           # Database helpers & migrations
│       ├── models.py       # Data models
│       ├── auth.py         # Authentication blueprint
│       ├── routes.py       # Main blueprint
│       ├── migrations/
│       ├── templates/
│       └── static/
├── tests/
├── wsgi.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
