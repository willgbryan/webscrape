import datetime
import asyncio

from backend.outputs import DataTable

async def run():
    start_time = datetime.datetime.now()

    task = 'what are some austin vc firms'
    sources = []

    config_path = None
    researcher = DataTable(query=task, source_urls=None, sources=sources, config_path=config_path)
    report = await researcher.run()

    end_time = datetime.datetime.now()
    print(f"Report generated in {end_time - start_time}")

    return report 

if __name__ == "__main__":
    asyncio.run(run())
