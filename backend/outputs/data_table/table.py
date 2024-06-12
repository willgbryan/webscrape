from backend.master.curator import Curator
from fastapi import WebSocket

class DataTable:
    def __init__(self, query: str, source_urls, columns, rows, config_path: str, websocket: WebSocket, upload: bool):
        self.query = query
        self.source_urls = source_urls
        self.columns = columns
        self.rows = rows
        self.config_path = config_path
        self.websocket = websocket
        self.upload = upload

    async def run(self):
        researcher = Curator(
            query=self.query, 
            source_urls=self.source_urls, 
            columns=self.columns, 
            rows=self.rows, 
            config_path=self.config_path, 
            websocket=self.websocket,
            upload=self.upload
        )
        print(f'table start cols: {self.columns}')

        await researcher.conduct_research()

        dataset = await researcher.create_rows()

        final_dataset = await researcher.fill_empty_rows(dataset)

        print(f'Run successful: {final_dataset}')

        return final_dataset
