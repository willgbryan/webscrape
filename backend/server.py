from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import os
import aiofiles
from typing import List
from backend.utils.websocket_manager import WebSocketManager
from utils import write_md_to_pdf
from fastapi.middleware.cors import CORSMiddleware


class ResearchRequest(BaseModel):
    task: str
    sources: List[str] = []


app = FastAPI()

origins = [
    "http://reach-next-app:3000",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# #TODO nothing todo just tagging as preserved for now while react migration is in progress
# app.mount("/site", StaticFiles(directory="./frontend"), name="site")
# app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")

# templates = Jinja2Templates(directory="./frontend")
# # app.mount("/", StaticFiles(directory="reach-react-app/build", html=True), name="react_app")

manager = WebSocketManager()

# Dynamic directory for outputs once first research is run
@app.on_event("startup")
def startup_event():
    if not os.path.isdir("outputs"):
        os.makedirs("outputs")
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# @app.get("/")
# async def read_root(request: Request):
#     return templates.TemplateResponse('index.html', {"request": request, "report": None})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("start"):
                json_data = json.loads(data[6:])
                task = json_data.get("task")
                sources = json_data.get("sources", [])
                
                if task:
                    report = await manager.start_streaming(task, sources, websocket)
                    path = await write_md_to_pdf(report)
                    await websocket.send_json({"type": "path", "output": path})
                else:
                    print("Error: not enough parameters provided.")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
