FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    MIKASA_API_HOST=0.0.0.0

WORKDIR /app

RUN addgroup --system mikasa && adduser --system --ingroup mikasa mikasa

COPY requirements-railway.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-railway.txt

COPY core/ ./core/
COPY supabase/ ./supabase/

RUN mkdir -p /app/data && chown -R mikasa:mikasa /app

USER mikasa

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + (__import__('os').environ.get('PORT','8080')) + '/health')" || exit 1

CMD ["python", "-m", "core.production_server"]
