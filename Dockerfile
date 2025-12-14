# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# --- 1. System Dependencies (CRITICAL FIX: MySQL Driver) ---
# Install system dependencies (gcc, default-libmysqlclient-dev) needed for MySQL drivers
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    # Clean up APT lists
    && rm -rf /var/lib/apt/lists/*
# Add this line anywhere before the COPY or pip install commands
RUN echo "Final Cache Buster" >> /tmp/cache_buster_file.txt

# --- 2. Copy Files (Application Code) ---
COPY requirements.txt .
COPY run.py .
# CRITICAL FIX: Copy the local 'app' directory to the container's WORKDIR (/app)
COPY app ./app

# --- 3. Python Dependencies ---
# Install Python dependencies from the requirements.txt file
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- 4. Security Setup ---
# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8000/health"] || exit 1

# --- 5. Application Entry Point (CRITICAL FIX: Correct Uvicorn path) ---
# Run the application, pointing Uvicorn to the FastAPI instance at app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]