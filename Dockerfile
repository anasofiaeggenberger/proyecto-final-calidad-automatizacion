FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt

COPY app.py ./
COPY api ./api
COPY domain ./domain
COPY services ./services
COPY static ./static
COPY templates ./templates

ARG APP_VERSION=desconocida
ENV APP_VERSION=${APP_VERSION} \
    APP_AMBIENTE=ci \
    PORT=8000

EXPOSE 8000

# un solo worker: la cola vive en memoria del proceso y no debe partirse entre réplicas
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --access-logfile - --error-logfile - app:app"]
