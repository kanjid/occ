# Dockerfile
FROM python:3.11-slim

# Evitar instalar como root en runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copiar sólo lo necesario (mejor con requirements separate)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/
COPY run.sh /app/run.sh
RUN chown -R appuser:appuser /app
USER appuser

# Ejecutar el entrypoint
ENTRYPOINT ["bash", "/app/run.sh"]
