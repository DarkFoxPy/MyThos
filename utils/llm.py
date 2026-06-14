"""
Wrapper LLM con fallback automático entre modelos.

Si el modelo principal falla por cuota (429), retry, o respuesta vacía,
intenta automáticamente con modelos alternativos en orden de preferencia.
Esto evita que la demo se rompa si un modelo agotó su cuota diaria.
"""
import time
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)


# Cadena de modelos a probar en orden si el primario falla por cuota
FALLBACK_CHAIN = [
    GEMINI_MODEL,             # primario: gemini-2.5-flash-lite
    "gemini-2.0-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-flash-latest",
]


def _is_quota_error(exc: Exception) -> bool:
    """Detecta si la excepción es por cuota agotada (429)."""
    msg = str(exc).lower()
    return any(k in msg for k in ("429", "quota", "exhausted", "rate", "exceeded"))


def _extract_text(response) -> str:
    """Extrae texto de una respuesta de Gemini con tolerancia a respuestas
    bloqueadas por safety o parciales."""
    try:
        txt = response.text or ""
        if txt.strip():
            return txt
    except (ValueError, AttributeError):
        pass
    try:
        cand = response.candidates[0] if response.candidates else None
        if cand and cand.content and cand.content.parts:
            return "".join(p.text for p in cand.content.parts if hasattr(p, "text"))
    except Exception:
        pass
    return ""


def generate(prompt: str, json_mode: bool = False, max_retries: int = 1) -> str:
    """
    Genera contenido con fallback automático entre modelos.

    Args:
        prompt: el prompt a enviar
        json_mode: si True, configura response_mime_type=application/json
        max_retries: reintentos por modelo antes de pasar al siguiente

    Returns:
        Texto generado por el primer modelo que responda con éxito.

    Raises:
        RuntimeError con un mensaje amigable si TODOS los modelos fallaron.
    """
    config = {"response_mime_type": "application/json"} if json_mode else {}
    last_err = None
    tried = []

    for model_name in FALLBACK_CHAIN:
        for attempt in range(max_retries + 1):
            try:
                gm = genai.GenerativeModel(model_name, generation_config=config)
                response = gm.generate_content(prompt)
                text = _extract_text(response)
                if text.strip():
                    return text
                # Respuesta vacía: pasar al siguiente modelo
                break
            except Exception as e:
                last_err = e
                if _is_quota_error(e):
                    # Cuota agotada en este modelo: pasar al siguiente sin retry
                    tried.append(model_name)
                    break
                # Otro error temporal: pequeño backoff y retry
                if attempt < max_retries:
                    time.sleep(0.8)
                else:
                    tried.append(model_name)
                    break

    # Todos los modelos fallaron
    raise RuntimeError(
        f"No se pudo procesar la consulta porque los modelos disponibles "
        f"alcanzaron su cuota diaria. Modelos probados: {', '.join(tried)}. "
        f"Por favor, intentá nuevamente en unos minutos."
    ) from last_err
