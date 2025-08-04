import uvicorn
from typing import Optional, List
from pathlib import Path

import websockets.exceptions

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from rggbar import state


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager: Optional[ConnectionManager] = None
template_path: Optional[str] = None
cfg: dict = {}

app = FastAPI()


@app.get("/init")
async def init():
    global cfg
    cfg = state.load()
    if cfg is None:
        cfg = {"platforms": {}}

    return cfg


@app.get("/", include_in_schema=False)
async def index(request: Request):
    templates = Jinja2Templates(directory=template_path)

    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except websockets.exceptions.ConnectionClosed:
        manager.disconnect(websocket)


def run(work_dir):
    global manager, template_path, cfg

    cfg = state.load()
    if cfg is None:
        cfg = {"platforms": {}}

    manager = ConnectionManager()

    template_path = Path(work_dir).joinpath("web")

    app.mount("/", StaticFiles(directory=template_path), name="static")
    uvicorn.run(app, host="localhost", port=6660, log_level="critical", workers=1)
