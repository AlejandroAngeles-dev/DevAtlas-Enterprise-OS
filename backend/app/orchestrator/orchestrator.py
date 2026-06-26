import json
import logging
from app.orchestrator.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

ORCHESTRATOR_PROMPT = """
Eres el orquestador central de DevAtlas Enterprise OS.
Tu única función es analizar el mensaje del usuario y decidir
qué agentes deben responder.

Los agentes disponibles son:

- atlas_coach: Analiza el estado general del negocio, detecta
  riesgos y oportunidades. Úsalo cuando el usuario pregunte
  por el estado de su empresa, métricas generales o quiera
  consejos de negocio.

- atlas_finance: Maneja finanzas, facturas, pagos y flujo de caja.
  Úsalo cuando el usuario pregunte por dinero, facturas,
  cobros o proyecciones financieras.

- atlas_connect: Envía mensajes por WhatsApp y Gmail.
  Úsalo cuando el usuario quiera comunicarse con clientes,
  enviar recordatorios o seguimientos.

Responde ÚNICAMENTE con un JSON válido con este formato exacto,
sin texto adicional, sin bloques de código markdown:
{
  "agents": ["nombre_agente1", "nombre_agente2"],
  "instructions": {
    "nombre_agente1": "instrucción específica para este agente",
    "nombre_agente2": "instrucción específica para este agente"
  },
  "reasoning": "explicación breve de por qué elegiste estos agentes"
}
"""


class Orchestrator:

    def __init__(self) -> None:
        # El orquestador usa Gemini sin tools — solo necesita razonar
        # y devolver JSON, no ejecutar funciones externas
        self.client = GeminiClient(system_prompt=ORCHESTRATOR_PROMPT)

    async def route(self, message: str) -> dict:
        """
        Recibe el mensaje del usuario y devuelve un diccionario
        con los agentes a activar y sus instrucciones.
        """
        logger.info(f"[Orchestrator] Routing: {message[:80]}...")

        try:
            raw = await self.client.send_message(message)
            # Limpiar posibles bloques markdown que Gemini añade a veces
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(clean)
            logger.info(f"[Orchestrator] Agents selected: {result.get('agents')}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[Orchestrator] JSON parse error: {e}. Raw: {raw}")
            # Fallback: si no puede parsear, manda al coach por defecto
            return {
                "agents": ["atlas_coach"],
                "instructions": {
                    "atlas_coach": message
                },
                "reasoning": "Fallback por error de parsing"
            }

        except Exception as e:
            logger.error(f"[Orchestrator] Error: {e}")
            return {
                "agents": ["atlas_coach"],
                "instructions": {"atlas_coach": message},
                "reasoning": f"Fallback por error: {str(e)}"
            }