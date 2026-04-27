from fastapi import FastAPI
from datetime import datetime, timezone
import os

app = FastAPI(title="App Python", version="1.0.0")


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
