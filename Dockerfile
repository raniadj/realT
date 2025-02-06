FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir setuptools wheel

WORKDIR /app

COPY last_offer/requirements.txt /app/last_offer/requirements.txt

RUN pip install --no-cache-dir -r last_offer/requirements.txt

COPY . /app

CMD ["python", "last_offer/last_offer.py"]
