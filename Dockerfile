FROM python:3.13.16-slim-trixie

# Apply available Debian security updates when rebuilding.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only runtime source belongs in the image, not local environments or reports.
COPY src/ ./src/
COPY wsgi.py ./wsgi.py

ENV PYTHONPATH=/app/src
ENV FLASK_APP=company_website

EXPOSE 7000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7000", "--access-logfile", "-", "wsgi:app"]
