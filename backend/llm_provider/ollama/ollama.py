import os

from litellm import completion
from colorama import Fore, Style


class OllamaProvider:

    def __init__(
        self,
        model,
        temperature,
        max_tokens
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def get_chat_response(self, messages, stream, webocket=None):
        if not stream:
            # Getting output from the model chain using ainvoke for asynchronous invoking
            response = completion(
                model=f"ollama_chat/{self.model}", 
                messages=[{"content": f"{messages}", "role": "user"}], 
                api_base="http://ollama:11434"
            )
            print(response)

            return response
        else:
            return await self.stream_response(messages, websocket)

    async def stream_response(self, messages, websocket=None):
        paragraph = ""
        response = ""

        response = await litellm.acompletion(
            model=f"ollama_chat/{self.mode}", 
            messages=[{f"content": "{messages}" ,"role": "user"}], 
            api_base="http://ollama:11434", 
            stream=True
        )
        async for chunk in response:
            if chunk is not None:
                response += chunk
                paragraph += chunk
                if "\n" in paragraph:
                    if websocket is not None:
                        await websocket.send_json({"type": "report", "output": paragraph})
                    else:
                        print(f"{Fore.GREEN}{paragraph}{Style.RESET_ALL}")
                    paragraph = ""
                print(chunk)
        
        return response
