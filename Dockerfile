# CPU-only lightweight container
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y build-essential git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build index on first run (optional): uncomment to auto-build
# RUN python build_index.py

CMD ["python", "app.py"]
