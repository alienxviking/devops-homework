FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

RUN useradd -m appuser
USER appuser

EXPOSE 5000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "app.main:app"]
