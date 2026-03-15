FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for lxml)
RUN apt-get update && apt-get install -y gcc libxml2-dev libxslt-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install schedule

COPY . .

# Create volume mount points
VOLUME ["/app/exports", "/app/data"]

# Environment variables
ENV PYTHONUNBUFFERED=1

# Default command runs the scheduler
CMD ["python", "scheduler.py"]
