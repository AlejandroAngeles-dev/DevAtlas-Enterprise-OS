import asyncio
import logging
from typing import AsyncGenerator

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

genai.configure(api_key=settings.gemini_api_key)


class GeminiClient:

    def __init__(
        self,
        system_prompt: str,
        tools: list | None = None,
    ) -> None:
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=system_prompt,
            tools=tools or [],
            generation_config=GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_output_tokens,
            ),
        )
        self._chat_session = None

    def start_chat(self, history: list | None = None) -> None:
        self._chat_session = self.model.start_chat(history=history or [])

    async def send_message(self, message: str) -> str:
        if not self._chat_session:
            self.start_chat()

        response = await asyncio.to_thread(
            self._chat_session.send_message, message
        )
        return response.text

    async def send_message_with_tools(self, message):
        if not self._chat_session:
            self.start_chat()

        response = await asyncio.to_thread(
            self._chat_session.send_message, message
        )
        return response

    async def stream_message(self, message: str) -> AsyncGenerator[str, None]:
        if not self._chat_session:
            self.start_chat()

        response = await asyncio.to_thread(
            self._chat_session.send_message,
            message,
            stream=True,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text