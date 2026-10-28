FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# Security hardening: run as a non-root user
RUN useradd --create-home appuser
USER appuser

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
