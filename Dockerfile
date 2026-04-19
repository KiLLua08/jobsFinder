# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (if needed for psycopg2 or selenium)
# Uncomment if build fails with psycopg2 or gcc-dependent packages
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libpq-dev \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Install pip dependencies from pyproject.toml
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run entrypoint
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
