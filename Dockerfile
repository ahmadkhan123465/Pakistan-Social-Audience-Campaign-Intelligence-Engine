FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# Hugging Face Spaces runs containers as non-root UID 1000
RUN useradd -m -u 1000 user

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user:user . .
RUN mkdir -p /app/data && chown -R user:user /app/data && chmod -R 775 /app/data

USER user

EXPOSE 7860

CMD ["sh", "-c", "gunicorn wsgi:app --bind 0.0.0.0:${PORT:-7860} --workers 1 --threads 4 --timeout 120"]
