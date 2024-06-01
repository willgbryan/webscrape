import os
import httpx
from colorama import Fore, Style

class CplusplusProvider:
    def __init__(self, model, temperature, max_tokens):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def get_chat_response(self, messages, stream, websocket=None):
        if not stream:
            response = await self.send_request(messages)
            print(response)
            return response
        else:
            return await self.stream_response(messages, websocket)

    async def send_request(self, messages):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url="http://inference-server:11434/completion",
                headers={"Content-Type": "application/json"},
                json={"prompt": messages, "n_predict": self.max_tokens}
            )
            response.raise_for_status()
            return response.json()

    async def stream_response(self, messages, websocket=None):
        paragraph = ""
        response = ""

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                url="http://inference-server:11434/completion",
                headers={"Content-Type": "application/json"},
                json={"prompt": messages, "n_predict": self.max_tokens}
            ) as stream_response:
                async for chunk in stream_response.aiter_text():
                    if chunk:
                        response += chunk
                        paragraph += chunk
                        if "\n" in paragraph:
                            if websocket:
                                await websocket.send_json({"type": "report", "output": paragraph})
                            else:
                                print(f"{Fore.GREEN}{paragraph}{Style.RESET_ALL}")
                            paragraph = ""
                        print(chunk)

        return response