# Build: docker build -t blk-hacking-ind-narender .
# Using Python 3.11-slim (Debian-based): small image,
# full C extension support for psutil, official LTS support

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5477

# Multiple workers for multi-core CPU utilization
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5477", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]
