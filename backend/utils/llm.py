from __future__ import annotations

import json
import logging
import asyncio
import time
import pandas as pd
from io import StringIO
from typing import Optional

from colorama import Fore, Style
from fastapi import WebSocket
from langchain_openai import ChatOpenAI


def get_provider(llm_provider):
    match llm_provider:
        case "openai":
            from ..llm_provider import OpenAIProvider
            llm_provider = OpenAIProvider
        case "ollama":
            from ..llm_provider import OllamaProvider
            llm_provider = OllamaProvider
        case "llama-cpp":
            from ..llm_provider import CplusplusProvider
            llm_provider = CplusplusProvider
        case _:
            raise Exception("LLM provider not found.")
    return llm_provider

async def create_chat_completion(
    messages: list,  # type: ignore
    model: Optional[str] = None,
    temperature: float = 1.0,
    max_tokens: Optional[int] = None,
    llm_provider: Optional[str] = None,
    stream: Optional[bool] = False,
    websocket: WebSocket | None = None,
) -> str:
    """Create a chat completion using the OpenAI API
    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.9.
        max_tokens (int, optional): The max tokens to use. Defaults to None.
        stream (bool, optional): Whether to stream the response. Defaults to False.
        llm_provider (str, optional): The LLM Provider to use.
        webocket (WebSocket): The websocket used in the currect request
    Returns:
        str: The response from the chat completion
    """
    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if max_tokens is not None and max_tokens > 8001:
        raise ValueError(
            f"Max tokens cannot be more than 8001, but got {max_tokens}")
    # Get the provider from supported providers
    ProviderClass = get_provider(llm_provider)
    provider = ProviderClass(
        model,
        temperature,
        max_tokens
    )
    # create response
    for _ in range(10):  # maximum of 10 attempts
        if llm_provider == "openai":
            response = await provider.get_chat_response(
                messages, stream, websocket
            )
        else:
            model_response = await provider.get_chat_response(
                messages, stream, websocket
            )
            response = model_response.choices[0].message['content']
        return response
    logging.error("Failed to get response from OpenAI API")
    raise RuntimeError("Failed to get response from OpenAI API")

async def parse_chat_completion_for_json(output: str | dict) -> pd.DataFrame:
    if isinstance(output, str):
        output = output.strip('```json').strip('```').strip()
        output_dict = json.loads(output)
    else:
        output_dict = output
    
    df = pd.DataFrame(output_dict)
    return df
