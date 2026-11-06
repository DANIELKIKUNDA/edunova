FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng libgl1 libglib2.0-0 curl && rm -rf /var/lib/apt/lists/* \
 && groupadd --system edunova && useradd --system --gid edunova --home /app edunova
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade "setuptools>=78.1.1" \
 && pip install --no-cache-dir -r requirements.txt
COPY --chown=edunova:edunova app ./app
USER edunova
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -fsS http://127.0.0.1:8000/v1/operations/live || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=127.0.0.1"]
