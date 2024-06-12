# connect any client to gpt-researcher using websocket
import asyncio
import datetime
import os
from typing import Dict, List

from fastapi import WebSocket

from backend.outputs import DataTable


class WebSocketManager:
    """Manage websockets"""
    def __init__(self):
        """Initialize the WebSocketManager class."""
        self.active_connections: List[WebSocket] = []
        self.sender_tasks: Dict[WebSocket, asyncio.Task] = {}
        self.message_queues: Dict[WebSocket, asyncio.Queue] = {}

    async def start_sender(self, websocket: WebSocket):
        """Start the sender task."""
        queue = self.message_queues.get(websocket)
        if not queue:
            return

        while True:
            message = await queue.get()
            if websocket in self.active_connections:
                try:
                    await websocket.send_text(message)
                except:
                    break
            else:
                break

    async def connect(self, websocket: WebSocket):
        """Connect a websocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.message_queues[websocket] = asyncio.Queue()
        self.sender_tasks[websocket] = asyncio.create_task(self.start_sender(websocket))

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.sender_tasks[websocket].cancel()
            await self.message_queues[websocket].put(None)
            del self.sender_tasks[websocket]
            del self.message_queues[websocket]

    async def start_streaming(self, task, columns, rows, websocket, upload):
        """Start streaming the output."""
        dataset = await iter_curate(task, columns, rows, websocket, upload)
        return dataset


async def iter_curate(task, columns, rows, websocket, upload):
    """Run the scrape"""
    start_time = datetime.datetime.now()
    print(f'stream start cols: {columns}')

    config_path = None
    researcher = DataTable(
        query=task, 
        source_urls=None, 
        columns=columns, 
        rows=rows,
        config_path=config_path, 
        websocket=websocket,
        upload=upload
    )
    dataset = await researcher.run()

    # Convert dataset to JSON
    dataset_json = dataset.to_json(orient="records")

    end_time = datetime.datetime.now()
    await websocket.send_json({"type": "logs", "output": f"\nTotal run time: {end_time - start_time}\n"})

    print(f'Dataset: {dataset_json}')
    return dataset_json
