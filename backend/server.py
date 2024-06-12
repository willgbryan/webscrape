from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import os
import aiofiles
import pandas as pd
from typing import List
from backend.utils.websocket_manager import WebSocketManager
from output_gen_utils import write_md_to_pdf
from fastapi.middleware.cors import CORSMiddleware


class ResearchRequest(BaseModel):
    task: str
    sources: List[str] = []


app = FastAPI()

origins = [
    "http://magi-next-app:3000",
    "http://localhost:3000",
    "https://magi-next-app:3000",
    "https://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = WebSocketManager()

# Dynamic directory for outputs once first research is run
@app.on_event("startup")
def startup_event():
    if not os.path.isdir("outputs"):
        os.makedirs("outputs")
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    print("WebSocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            if data.startswith("start"):
                json_data = json.loads(data[6:])
                task = json_data.get("task")
                columns = json_data.get("columnHeaders")
                rows = json_data.get("rowCount")
                print(f"Parsed task: {task}, columns: {columns}, rows: {rows}")

                # upload = True if a file has been uploaded as the env variable will exist, otherwise its false
                upload = "UPLOADED_FILE_PATH" in os.environ

                if task:
                    report = await manager.start_streaming(task, columns, rows, websocket, upload)
                    await websocket.send_json({"type": "dataset", "output": report})
                    print(f"report: {report}")
                else:
                    print("Error: not enough parameters provided.")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    try:
        if file.content_type not in ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            raise HTTPException(status_code=400, detail="Invalid file type")

        if file.content_type == "text/csv":
            df = pd.read_csv(file.file)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(file.file)

        output_path = os.path.join("outputs", file.filename)
        df.to_csv(output_path, index=False)

        os.environ["UPLOADED_FILE_PATH"] = output_path

        return {"filename": file.filename, "message": "File uploaded successfully", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
