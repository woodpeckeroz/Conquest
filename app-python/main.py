from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from datetime import datetime, timezone
import time as time_module
import os
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="App Python", version="1.0.0")

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)
    start = time_module.perf_counter()
    response = await call_next(request)
    duration = time_module.perf_counter() - start
    REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
    REQUEST_DURATION.labels(request.method, request.url.path).observe(duration)
    return response


@app.get("/health")
def health():
    return {
        "message": "Hello from Python App — running and healthy!",
        "app": "app-python",
    }


@app.get("/time")
def current_time():
    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "app": "app-python",
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
