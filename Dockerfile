# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Set work directory
WORKDIR /app

# Install system dependencies (if needed for psycopg2 or selenium)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libpq-dev \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml .

# Install dependencies
# If uv.lock doesn't exist yet, we can use `uv pip install -r pyproject.toml` or similar, 
# but `uv sync` is preferred if lock exists. 
# For initialization without lock, we can use `uv pip install --system .` or similar logic.
# Here we'll assume we generate lock file or install from toml.
RUN uv pip install --system -r pyproject.toml || uv pip install --system django psycopg2-binary selenium transformers torch

COPY . .

# Run entrypoint
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
