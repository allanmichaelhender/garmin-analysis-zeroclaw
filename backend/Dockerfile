FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run database migrations
RUN python -c "from app.core.database import init_db; init_db()"

# Expose port
EXPOSE 8000

# Run FastAPI app (for health checks)
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
