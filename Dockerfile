# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies REQUIRED for PyTorch and HuggingFace
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# MAGIC TRICK: Copy 'uv' directly from its official image into our container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies using UV instead of pip
# --system tells uv to install globally instead of making a venv inside the container
COPY pyproject.toml .
# If you have a uv.lock file in your project, uncomment the next line:
# COPY uv.lock .
RUN uv pip install --system --no-cache -e ".[ml]"

COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run entrypoint
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]