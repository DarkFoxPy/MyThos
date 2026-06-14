"""
Apollo — NLP Engine
Intent detection + semantic parsing + query normalization.

Recibe el lenguaje informal del empleado y lo convierte en una estructura
semántica precisa antes de que llegue a Atlas o Athena.
Resuelve la Falla 6 del Entregable 1: estandariza el proceso independientemente
de cómo formule la pregunta cada empleado.
"""
import json
from utils.llm import generate as llm_generate

# Intenciones posibles que Apollo puede clasificar
INTENTS = {
    "document_query":   "consulta sobre documentos o políticas de la empresa",
    "module_complete":  "el empleado indica que terminó de leer el módulo",
    "difficulty":       "el empleado expresa que no entiende o tiene dificultades",
    "greeting":         "saludo o mensaje de cortesía sin consulta",
    "out_of_domain":    "pregunta que no está relacionada con el trabajo ni los documentos",
    "progress_check":   "el empleado pregunta sobre su propio avance o estado",
}

APOLLO_PROMPT = """Sos Apollo, el motor NLP del sistema Mythos.
Tu tarea es analizar el mensaje de un empleado nuevo durante su proceso de inducción
y clasificarlo con precisión.

MENSAJE DEL EMPLEADO: "{message}"

Clasificá el mensaje y respondé ÚNICAMENTE con este JSON (sin texto adicional):
{{
  "intent": "document_query|module_complete|difficulty|greeting|out_of_domain|progress_check",
  "topic": "tema principal del mensaje (ej: licencias, horarios, reglamento, o null si no aplica)",
  "normalized_query": "versión formal y completa de la pregunta, lista para buscar en documentos (null si intent no es document_query)",
  "entities": ["lista de términos clave extraídos"],
  "confidence": 0.0
}}

Criterios:
- "document_query": preguntas SOBRE el CONTENIDO de los documentos de la empresa (políticas,
  procedimientos, beneficios, normas, horarios, licencias, código de conducta). El empleado
  pregunta por algo que está o debería estar en el reglamento o manual de la empresa.
- "module_complete": frases como "ya terminé", "listo el módulo", "terminé de leer"
- "difficulty": "no entendí", "no sé", "está difícil", "no entiendo nada"
- "greeting": "hola", "buenos días", "gracias", mensajes sin consulta
- "out_of_domain": preguntas que NO son sobre el contenido corporativo. Esto incluye:
   · preguntas sobre el SISTEMA MYTHOS mismo (ej: "qué es Mythos", "qué agentes tiene",
     "quién sos", "cómo funciona el software", "por qué no usar Excel")
   · preguntas técnicas del producto, arquitectura, modelos de IA
   · preguntas personales del asistente ("quién sos", "cómo te llamás")
   · preguntas sobre temas externos: fútbol, clima, política, vida personal
   · cualquier consulta meta sobre el funcionamiento de la inducción/plataforma
- "progress_check": "cómo voy", "qué me falta", "cuánto llevo"
- confidence: entre 0.0 y 1.0, qué tan seguro estás de la clasificación

REGLA CRÍTICA: Si el empleado pregunta SOBRE EL SISTEMA, sobre los agentes (Athena, Atlas,
Apollo, Artemis), sobre tecnología usada, o cualquier cosa meta del producto, eso SIEMPRE
es "out_of_domain". El asistente solo responde consultas sobre el contenido corporativo
real de la empresa, no sobre sí mismo."""


def parse(message: str, lang: str = "es") -> dict:
    """
    Procesa el mensaje del empleado y retorna la estructura semántica.

    Returns:
        {
            intent: str,
            topic: str | None,
            normalized_query: str | None,
            entities: list[str],
            confidence: float,
            original: str
        }
    """
    prompt = APOLLO_PROMPT.format(message=message)

    parsed = {}
    try:
        text = llm_generate(prompt, json_mode=True, max_retries=1).strip()
        if text:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                s, e = text.find("{"), text.rfind("}") + 1
                if s >= 0 and e > s:
                    try:
                        parsed = json.loads(text[s:e])
                    except json.JSONDecodeError:
                        parsed = {}
    except Exception:
        # Si todos los modelos fallan, asumimos document_query y dejamos que Atlas
        # responda con sus propios fallbacks (que también usan llm_generate)
        parsed = {}

    parsed["original"] = message

    # Valores por defecto si Gemini devuelve estructura incompleta
    parsed.setdefault("intent", "document_query")
    parsed.setdefault("topic", None)
    parsed.setdefault("normalized_query", message)
    parsed.setdefault("entities", [])
    parsed.setdefault("confidence", 0.5)

    return parsed


def get_search_query(parsed: dict) -> str:
    """Retorna la query normalizada para Atlas, o el mensaje original como fallback."""
    return parsed.get("normalized_query") or parsed.get("original", "")


def is_document_query(parsed: dict) -> bool:
    return parsed.get("intent") == "document_query"


def is_difficulty_signal(parsed: dict) -> bool:
    return parsed.get("intent") == "difficulty"


def is_module_complete(parsed: dict) -> bool:
    return parsed.get("intent") == "module_complete"
