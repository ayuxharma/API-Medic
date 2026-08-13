# syntax=docker/dockerfile:1

# Use a small official Python 3.13 environment.
FROM python:3.13-slim

# Do not create .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Send Python logs directly to the container output.
ENV PYTHONUNBUFFERED=1

# Create and select the application directory.
WORKDIR /app

# Copy dependencies separately for better build caching.
COPY requirements.txt .

# Install packages required at runtime.
RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt

# Copy the application into the image.
COPY agent ./agent
COPY web ./web
COPY templates ./templates
COPY static ./static
COPY app.py .

# Create a normal user instead of running as root.
RUN useradd \
    --create-home \
    --uid 10001 \
    appuser

USER appuser

# Document the FastAPI port.
EXPOSE 8000

# Ask Docker to monitor the health endpoint.
HEALTHCHECK \
    --interval=30s \
    --timeout=3s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).close()"]

# Start FastAPI when the container starts.
CMD ["python", "-m", "uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]