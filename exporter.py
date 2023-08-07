from settings import Settings

import asyncio
from fastapi import FastAPI, WebSocket, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.websockets import WebSocketDisconnect
from fastapi.templating import Jinja2Templates

from pathlib import Path


app = FastAPI()
security = HTTPBasic()
template_path = Path(__file__).parent / 'templates'
templates = Jinja2Templates(directory=str(template_path.resolve()))


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    if password != "ymm0205":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return username


@app.get("/")
async def index():
    return RedirectResponse('/v')


@app.get("/{realm}")
async def log_page(realm: str, request: Request, username: str = Depends(get_current_username)):
    if realm not in ('v', 'j'):
        raise HTTPException(status_code=404, detail="realm must be 'v' or 'j'")
    exporter_url = f'wss://{Settings.exporter_ip}:{Settings.exporter_port}/{realm}/ws'
    return templates.TemplateResponse("index.html", {"request": request, 'exporter_url': exporter_url})


@app.websocket("/{realm}/ws")
async def websocket_endpoint(realm: str, websocket: WebSocket):
    await websocket.accept()
    try:
        log_file_path = Settings.v2ray_log_path if realm == 'v' else Settings.jmssub_log_path
        with open(log_file_path, 'r') as reader:
            while True:
                line = reader.readline().strip()
                if not line:
                    await asyncio.sleep(3)
                else:
                    await websocket.send_text(line)
    except WebSocketDisconnect:
        pass


