
import logging
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from app.database import get_connection, init_db


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("pulseops")

started_at = time.monotonic()

metrics = {
    "requests": 0,
    "errors": 0
}

Status = Literal[
    "pending",
    "preparing",
    "completed",
    "cancelled"
]


# ==========================================
# PROMETHEUS METRICS
# ==========================================

REQUEST_COUNT = Counter(
    "pulseops_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "pulseops_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

SERVER_ERRORS = Counter(
    "pulseops_server_errors_total",
    "Total HTTP server errors"
)


# ==========================================
# PYDANTIC MODELS
# ==========================================

class OrderCreate(BaseModel):
    item: str = Field(min_length=1, max_length=100)
    status: Status = "pending"


class OrderUpdate(BaseModel):
    item: str = Field(min_length=1, max_length=100)
    status: Status


# ==========================================
# DATABASE STARTUP
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="PulseOps API",
    version="1.1.0",
    lifespan=lifespan
)


# ==========================================
# MONITORING MIDDLEWARE
# ==========================================

@app.middleware("http")
async def monitor(request: Request, call_next):

    metrics["requests"] += 1
    start = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code

        if status_code >= 500:
            metrics["errors"] += 1
            SERVER_ERRORS.inc()

        return response

    except Exception:
        metrics["errors"] += 1
        SERVER_ERRORS.inc()
        logger.exception("Unhandled request failure")
        raise

    finally:
        duration = time.perf_counter() - start

        route = request.scope.get("route")
        endpoint = (
            route.path
            if route is not None
            else "unmatched"
        )

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        logger.info(
            "%s %s -> %s (%.3fs)",
            request.method,
            endpoint,
            status_code,
            duration
        )


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )


# ==========================================
# JSON METRICS
# ==========================================

@app.get("/metrics")
def get_metrics():

    return {
        "requests_since_start": metrics["requests"],
        "server_errors_since_start": metrics["errors"],
        "uptime_seconds": round(
            time.monotonic() - started_at, 1
        )
    }


# ==========================================
# PROMETHEUS ENDPOINT
# ==========================================

@app.get("/prometheus", include_in_schema=False)
def prometheus_metrics():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ==========================================
# GET ALL ORDERS
# ==========================================

@app.get("/orders")
def list_orders():

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, item, status FROM orders ORDER BY id"
        ).fetchall()

    return [dict(row) for row in rows]


# ==========================================
# GET SINGLE ORDER
# ==========================================

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, item, status FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return dict(row)


# ==========================================
# CREATE ORDER
# ==========================================

@app.post("/orders", status_code=201)
def create_order(order: OrderCreate):

    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO orders (item, status) VALUES (?, ?)",
            (order.item, order.status)
        )

        order_id = cursor.lastrowid

    return {
        "id": order_id,
        **order.model_dump()
    }


# ==========================================
# UPDATE ORDER
# ==========================================

@app.put("/orders/{order_id}")
def update_order(order_id: int, order: OrderUpdate):

    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE orders SET item = ?, status = ? WHERE id = ?",
            (order.item, order.status, order_id)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

    return {
        "id": order_id,
        **order.model_dump()
    }


# ==========================================
# DELETE ORDER
# ==========================================

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM orders WHERE id = ?",
            (order_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

    return {
        "message": "Order deleted",
        "id": order_id
    }
