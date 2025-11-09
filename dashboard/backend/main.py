from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import asyncio
import json
import psutil
import socket
import os
from datetime import datetime
from typing import Dict, List
import zmq
import numpy as np
from pydantic import BaseModel

app = FastAPI(title="Hybrid IDS Dashboard", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: List[WebSocket] = []

# ZMQ setup for receiving alerts
context = zmq.Context()
zmq_subscriber = context.socket(zmq.SUB)
zmq_subscriber.connect("tcp://localhost:5556")  # Default port for Hybrid IDS alerts
zmq_subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

class Alert(BaseModel):
    timestamp: str
    source: str
    type: str
    severity: str
    message: str
    details: dict = {}

class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: float
    network_recv: float

async def get_system_metrics() -> SystemMetrics:
    return SystemMetrics(
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        disk_percent=psutil.disk_usage('/').percent,
        network_sent=psutil.net_io_counters().bytes_sent / (1024 * 1024),  # MB
        network_recv=psutil.net_io_counters().bytes_recv / (1024 * 1024),  # MB
    )

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Send system metrics every second
            metrics = await get_system_metrics()
            await websocket.send_json({"type": "metrics", "data": metrics.dict()})
            
            # Check for new alerts
            try:
                alert = await asyncio.get_event_loop().run_in_executor(
                    None, zmq_subscriber.recv_json, zmq.NOBLOCK
                )
                await websocket.send_json({"type": "alert", "data": alert})
            except zmq.Again:
                pass
                
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        active_connections.remove(websocket)

@app.get("/api/alerts")
async def get_recent_alerts(limit: int = 20):
    # In a real app, this would query a database
    return {"alerts": []}

@app.get("/api/metrics")
async def get_current_metrics():
    return await get_system_metrics()

# Serve frontend files
app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    return FileResponse("../frontend/build/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
