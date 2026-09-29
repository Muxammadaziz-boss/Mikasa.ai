FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    MISA_API_HOST=0.0.0.0

WORKDIR /app

RUN addgroup --system misa && adduser --system --ingroup misa misa

COPY requirements-railway.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-railway.txt

COPY core/ ./core/
COPY supabase/ ./supabase/

RUN mkdir -p /app/data && chown -R misa:misa /app

USER misa

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + (__import__('os').environ.get('PORT','8080')) + '/health')" || exit 1

CMD ["python", "-m", "core.production_server"]
