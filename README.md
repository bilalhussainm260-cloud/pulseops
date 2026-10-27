# PulseOps

A Python FastAPI order-management API demonstrating SQLite persistence, request logging, basic process-local metrics, automated tests, Docker, and GitHub Actions CI.

## Local setup

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API documentation.

## Endpoints

- `GET /health` - application and database health
- `GET /metrics` - basic process-local request count, server errors and uptime
- `GET /orders` - list orders
- `GET /orders/{id}` - fetch order
- `POST /orders` - create order
- `PUT /orders/{id}` - update order
- `DELETE /orders/{id}` - delete order

## Tests

```bash
python -m pytest -q
```

## Docker

```bash
docker build -t pulseops .
docker run --rm -p 8000:8000 pulseops
```

SQLite inside this default container is ephemeral. For persistent Docker data, mount a writable volume at `/app` or configure a separate database path and writable volume. This demo is single-instance only. Metrics reset on restart and are not Prometheus metrics.
