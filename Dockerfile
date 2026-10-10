FROM python:3.13.16-slim-trixie

# Apply available Debian security updates when rebuilding.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Remove an unused terminal library; do not force-remove essential Debian tools.
RUN apt-get purge -y libncursesw6

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m pip uninstall -y pip

# Only runtime source belongs in the image, not local environments or reports.
COPY src/ ./src/
COPY wsgi.py ./wsgi.py

ENV PYTHONPATH=/app/src
ENV FLASK_APP=company_website
ENV PYTHONDONTWRITEBYTECODE=1

# Numeric identity avoids needing account-management tools at runtime.
RUN mkdir -p /app/data && chown 10001:10001 /app/data
USER 10001:10001

EXPOSE 7000

# Initialize SQLite once before workers fork, avoiding concurrent migrations.
CMD ["gunicorn", "--preload", "-w", "2", "-b", "0.0.0.0:7000", "--access-logfile", "-", "wsgi:app"]
