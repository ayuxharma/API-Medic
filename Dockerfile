# syntax=docker/dockerfile:1

# Use a lightweight official Python environment.
FROM python:3.13-slim

# Do not create unnecessary Python bytecode files.
ENV PYTHONDONTWRITEBYTECODE=1

# Send logs immediately to the container output.
ENV PYTHONUNBUFFERED=1

# Use port 8000 unless the hosting platform overrides it.
ENV PORT=8000

# Create and select the application directory.
WORKDIR /app

# Copy dependencies separately for Docker build caching.
COPY requirements.txt .

# Install only production dependencies.
RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt

# Copy the application files.
COPY agent ./agent
COPY web ./web
COPY templates ./templates
COPY static ./static
COPY app.py .

# Run the application as a normal Linux user.
RUN useradd \
    --create-home \
    --uid 10001 \
    appuser

USER appuser

# Document the application's default port.
EXPOSE 8000

# Ask Docker to check whether FastAPI is responding.
HEALTHCHECK \
    --interval=30s \
    --timeout=3s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2).close()"]

# Start FastAPI using the port supplied by the environment.
CMD ["sh", "-c", "exec python -m uvicorn web.main:app --host 0.0.0.0 --port ${PORT:-8000}"]