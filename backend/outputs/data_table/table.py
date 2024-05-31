from backend.master.curator import Curator
from fastapi import WebSocket

class DataTable():
    def __init__(self, query: str, source_urls, sources, config_path: str, websocket: WebSocket):
        self.query = query
        self.source_urls = source_urls
        self.sources = sources
        self.config_path = config_path
        self.websocket = websocket

    async def run(self):
        researcher = Curator(self.query, self.source_urls, self.sources, self.config_path, self.websocket)

        await researcher.conduct_research()

        report = await researcher.create_dataset()

        return report 