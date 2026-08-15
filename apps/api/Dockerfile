FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir --requirement requirements.lock

COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY src ./src

RUN mkdir -p /app/data/knowledge && chown -R app:app /app/data/knowledge

USER app
EXPOSE 8000

CMD ["uvicorn", "sari_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
