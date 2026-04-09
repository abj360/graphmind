FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY extract ./extract
COPY resolution ./resolution
COPY load ./load

CMD ["python", "-m", "load.cdc_poller"]
