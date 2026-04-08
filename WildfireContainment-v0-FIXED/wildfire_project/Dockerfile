FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone OpenEnv source (needed for env_server internals)
RUN git clone https://github.com/meta-pytorch/OpenEnv.git /openenv
ENV PYTHONPATH="/openenv/src:/openenv:/app:${PYTHONPATH}"

# Copy project
COPY . .

# HF Spaces runs as non-root user 1000
RUN useradd -m -u 1000 user
USER user

# HF Spaces exposes port 7860
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
