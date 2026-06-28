"""
Mnemosyne — Knowledge Capture Agent
Entrevista guiada + síntesis documental + indexación en el RAG.

Resuelve la causa raíz del Entregable 1: "documentar genera un costo de tiempo
que la empresa no está dispuesta a asumir". Mnemosyne extrae el conocimiento
TÁCITO del supervisor (cómo se hace el trabajo del puesto, que no está en ningún
manual) mediante preguntas guiadas, lo estructura en un documento y lo indexa.

A partir de ahí ese conocimiento queda disponible para:
  - Atlas (responde consultas de los empleados con ese material)
  - la generación de rutas de onboarding
  - los cuestionarios de Artemis

Así el supervisor "enseña" una sola vez y Mythos transfiere ese conocimiento
sin volver a consumir su tiempo productivo.
"""
import json
import uuid
from utils.llm import generate as llm_generate
from utils.i18n import lang_name
from utils import processor


# ── Función A: Generación de preguntas guiadas ────────────────────────────────

QUESTIONS_PROMPT = """Sos Mnemosyne, el agente de captura de conocimiento del sistema Mythos.
Un supervisor quiere enseñarle a Mythos el conocimiento operativo de un puesto o tema,
de modo que los empleados nuevos puedan aprenderlo sin depender de su tiempo.

TEMA O PUESTO A DOCUMENTAR: "{topic}"

Generá entre 5 y 7 preguntas claras, concretas y ordenadas que, al ser respondidas por
el supervisor, permitan documentar CÓMO se hace ese trabajo. Cubrí (según aplique):
- Cuáles son las tareas y responsabilidades principales del puesto.
- El paso a paso de los procesos clave (cómo se hace cada cosa, en orden).
- Qué herramientas, sistemas o accesos se usan y para qué.
- Criterios de calidad: cómo se sabe que una tarea está bien hecha.
- Errores comunes que hay que evitar y cómo prevenirlos.
- A quién recurrir o qué hacer ante una duda o excepción.

Las preguntas deben ser específicas (no genéricas), accionables, y redactadas en {response_language}.

Respondé ÚNICAMENTE con este JSON (sin texto adicional):
{{
  "preguntas": ["pregunta 1", "pregunta 2", "..."]
}}"""


def generate_questions(topic: str, lang: str = "es") -> list[str]:
    """Devuelve una lista de preguntas guiadas para capturar el conocimiento del tema."""
    prompt = QUESTIONS_PROMPT.format(topic=topic, response_language=lang_name(lang))
    text = llm_generate(prompt, json_mode=True, max_retries=1)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        t2 = text.strip()
        s, e = t2.find("{"), t2.rfind("}") + 1
        data = json.loads(t2[s:e]) if s >= 0 else {}

    preguntas = [q for q in data.get("preguntas", []) if isinstance(q, str) and q.strip()]
    if not preguntas:
        raise RuntimeError("Mnemosyne no pudo generar preguntas. Probá reformular el tema.")
    return preguntas


# ── Función B: Síntesis del documento ─────────────────────────────────────────

SYNTH_PROMPT = """Sos Mnemosyne, el agente de captura de conocimiento del sistema Mythos.
Convertí la siguiente entrevista a un supervisor en un DOCUMENTO DE REFERENCIA claro y
estructurado, dirigido a un empleado nuevo, sobre el tema: "{topic}".

REGLAS:
- Usá ÚNICAMENTE la información de las respuestas. NO inventes datos, pasos ni nombres.
- Si una respuesta está vacía o es muy pobre, omití esa sección (no la inventes).
- Estructurá con títulos y viñetas claras, en lenguaje directo para alguien que recién ingresa.
- Conservá los detalles operativos concretos (pasos, herramientas, criterios, advertencias).
- Redactá todo en {response_language}.

ENTREVISTA (pregunta → respuesta del supervisor):
{qa_block}

Devolvé SOLO el texto del documento (con formato markdown simple), sin comentarios adicionales."""


def synthesize_document(topic: str, qa_pairs: list[dict], lang: str = "es") -> str:
    """
    qa_pairs: lista de {"pregunta": str, "respuesta": str}.
    Devuelve el texto estructurado del documento.
    """
    answered = [p for p in qa_pairs if (p.get("respuesta") or "").strip()]
    if not answered:
        raise ValueError("No hay respuestas para sintetizar. Completá al menos una pregunta.")

    qa_block = "\n\n".join(
        f"P: {p['pregunta']}\nR: {p['respuesta'].strip()}" for p in answered
    )
    prompt = SYNTH_PROMPT.format(topic=topic, qa_block=qa_block, response_language=lang_name(lang))
    text = llm_generate(prompt, json_mode=False, max_retries=1).strip()

    if not text:
        # Fallback: si el LLM no responde, guardamos la entrevista cruda estructurada.
        text = f"# {topic}\n\n" + "\n\n".join(
            f"## {p['pregunta']}\n{p['respuesta'].strip()}" for p in answered
        )
    return text


# ── Función C: Persistencia + indexación en el RAG ────────────────────────────

def save_knowledge(topic: str, document_text: str, company_id: str, db) -> dict:
    """
    Crea un documento etiquetado como captura y lo indexa en pgvector.
    Queda disponible de inmediato para Atlas, las rutas y los cuestionarios.
    Devuelve {document_id, filename, chunks}.
    """
    doc_id = str(uuid.uuid4())
    filename = f"[Captura] {topic}".strip()

    db.table("documents").insert({
        "id":           doc_id,
        "company_id":   company_id,
        "filename":     filename,
        "storage_path": f"capture/{company_id}/{doc_id}",
        "processed":    False,
    }).execute()

    n_chunks = processor.index_text(document_text, doc_id, company_id, db)
    return {"document_id": doc_id, "filename": filename, "chunks": n_chunks}


def capture(topic: str, qa_pairs: list[dict], company_id: str, db, lang: str = "es") -> dict:
    """Pipeline completo: sintetiza el documento desde la entrevista y lo indexa."""
    document_text = synthesize_document(topic, qa_pairs, lang=lang)
    result = save_knowledge(topic, document_text, company_id, db)
    result["document_text"] = document_text
    return result
