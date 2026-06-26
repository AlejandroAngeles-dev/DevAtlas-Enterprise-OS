import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import google.generativeai as genai

from app.orchestrator.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    success: bool
    content: str
    actions: list[dict] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    error: str | None = None


class BaseAgent(ABC):

    name: str = "base_agent"
    MAX_ITERATIONS: int = 5

    def __init__(self) -> None:
        self.client = GeminiClient(
            system_prompt=self.system_prompt,
            tools=self.tools,
        )

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @property
    @abstractmethod
    def tools(self) -> list: ...

    @abstractmethod
    async def execute_tool(self, tool_name: str, tool_args: dict) -> Any: ...

    async def run(
        self,
        message: str,
        context: dict | None = None,
        history: list | None = None,
    ) -> AgentResult:
        logger.info(f"[{self.name}] message: {message[:80]}...")
        self.client.start_chat(history=history)

        current_message = self._build_message(message, context)
        actions_taken = []

        for iteration in range(self.MAX_ITERATIONS):
            try:
                response = await self.client.send_message_with_tools(current_message)
            except Exception as e:
                logger.error(f"[{self.name}] Error: {e}")
                return AgentResult(
                    success=False,
                    content="Tuve un problema al procesar tu solicitud. Intenta de nuevo.",
                    error=str(e),
                )

            parts = response.candidates[0].content.parts
            function_call_part = next(
                (p for p in parts if hasattr(p, "function_call") and p.function_call.name),
                None,
            )

            if function_call_part is None:
                return AgentResult(
                    success=True,
                    content=response.text,
                    actions=actions_taken,
                )

            fc = function_call_part.function_call
            tool_name = fc.name
            tool_args = dict(fc.args)

            logger.info(f"[{self.name}] Ejecutando tool: {tool_name}")

            try:
                tool_result = await self.execute_tool(tool_name, tool_args)
                success = True
            except Exception as e:
                tool_result = {"error": str(e)}
                success = False

            actions_taken.append({
                "tool": tool_name,
                "args": tool_args,
                "result": tool_result,
                "success": success,
            })

            current_message = genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=tool_name,
                    response={"result": tool_result},
                )
            )

        return AgentResult(
            success=False,
            content="No pude completar la tarea. Intenta con una solicitud más específica.",
            actions=actions_taken,
            error="Max iterations reached",
        )

    def _build_message(self, message: str, context: dict | None) -> str:
        if not context:
            return message
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
        return f"CONTEXTO:\n{context_str}\n\nTAREA:\n{message}"