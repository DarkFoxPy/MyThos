"""
Atlas — RAG System
Vector DB + semantic retrieval + grounded generation.

Responde preguntas usando EXCLUSIVAMENTE los documentos indexados de la empresa.
No inventa. No generaliza. Si la respuesta no está, lo dice explícitamente.
Resuelve las Fallas 1, 2, 4, 5 y 10 del Entregable 1.
"""
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, RAG_THRESHOLD, RAG_TOP_K
from utils.processor import embed_query
from utils.i18n import t_lang, lang_name

genai.configure(api_key=GEMINI_API_KEY)

ATLAS_SYSTEM_PROMPT = """Sos Atlas, el asistente de conocimiento corporativo del sistema Mythos.
Tu función es responder preguntas de empleados nuevos usando ÚNICAMENTE la información
de los documentos internos de la empresa que se te proporcionan como contexto.

REGLAS ABSOLUTAS:
1. Solo respondé con información que aparezca en los FRAGMENTOS DE DOCUMENTOS que recibís.
2. Si la respuesta no está en los fragmentos, decí claramente que no la encontraste y sugerí consultar al supervisor.
3. Nunca inventes políticas, fechas, montos, procedimientos ni nombres.
4. Cuando uses información de un fragmento, indicá de dónde viene cuando sea útil.
5. Respondé de forma clara, amigable y directa para alguien que recién ingresa.
6. IMPORTANTE — Respondé SIEMPRE en {response_language}, sin importar el idioma de los documentos ni de la pregunta.
7. Si la pregunta es ambigua, pedí una aclaración breve antes de responder.

CÓMO ESTRUCTURAR LA RESPUESTA:
- Si el empleado hace VARIAS preguntas en un solo mensaje (separadas por "y", "?", o comas),
  respondé CADA UNA por separado, en orden, de forma explícita. No omitas ninguna parte.
- Si la pregunta describe un ESCENARIO CONCRETO (ej: "qué pasa si llego a las 10:30 a un mensaje
  que llegó a las 9:00"), no te limites a citar la política: APLICÁ la regla al escenario
  específico. Hacé el cálculo o la comparación necesaria y decí explícitamente "en tu caso, sí/no",
  citando los números relevantes.
- Si el escenario incumple una política, decilo de manera clara y mencioná la consecuencia
  concreta (descuento, sanción, etc.) tal como aparece en el documento.
- Si el escenario cumple la política, también decilo claramente.
- Usá viñetas o numeración cuando haya varias preguntas o varios puntos a tratar.

EJEMPLOS DE BUENA RESPUESTA APLICADA:
Pregunta del empleado: "¿qué pasa si llego a las 10:30 am a un mensaje que me llegó a las 9 am?"
Buena respuesta: "Entre las 9:00 y las 10:30 transcurren 90 minutos. Según el documento, el
tiempo máximo de respuesta a mensajes institucionales es de 15 minutos durante el horario
laboral, por lo tanto en tu caso estarías excediendo el plazo en 75 minutos, lo que constituye
un incumplimiento del reglamento de trabajo remoto."

Mala respuesta (NO HAGAS ESTO): "El tiempo máximo de respuesta es de 15 minutos durante el
horario laboral." (esto cita la regla pero no la aplica al caso del empleado)"""


def retrieve(query: str, company_id: str, db) -> list[dict]:
    """Busca los fragmentos más relevantes para la query usando similitud coseno en pgvector."""
    query_embedding = embed_query(query)
    result = db.rpc("match_documents", {
        "query_embedding":  query_embedding,
        "match_company_id": company_id,
        "match_threshold":  RAG_THRESHOLD,
        "match_count":      RAG_TOP_K,
    }).execute()
    return result.data or []


def generate_response(
    query: str,
    company_id: str,
    employee_id: str,
    module_id: str | None,
    db,
    chat_history: list[dict] | None = None,
    intent_context: dict | None = None,
    lang: str = "es",
) -> str:
    """
    Pipeline RAG completo:
    1. Recupera fragmentos relevantes de pgvector
    2. Construye el prompt con contexto corporativo real
    3. Genera la respuesta con Gemini (grounded en documentos)
    4. Guarda el intercambio en el historial
    """
    chunks = retrieve(query, company_id, db)

    if chunks:
        context = "\n\n---\n\n".join(c["content"] for c in chunks)
        context_block = f"FRAGMENTOS DE DOCUMENTOS DE LA EMPRESA:\n\n{context}"
    else:
        context_block = (
            "No se encontraron fragmentos relevantes en los documentos para esta consulta."
        )

    history_block = ""
    if chat_history:
        recent = chat_history[-6:]
        lines = [
            f"{'Empleado' if m['role'] == 'user' else 'Atlas'}: {m['content']}"
            for m in recent
        ]
        history_block = "\nHISTORIAL RECIENTE DE LA CONVERSACIÓN:\n" + "\n".join(lines)

    topic_hint = ""
    if intent_context and intent_context.get("topic"):
        topic_hint = f"\nTema identificado por Apollo: {intent_context['topic']}"

    sys_prompt = ATLAS_SYSTEM_PROMPT.format(response_language=lang_name(lang))
    prompt = f"""{sys_prompt}

{context_block}
{history_block}
{topic_hint}

PREGUNTA DEL EMPLEADO: {query}

RESPUESTA DE ATLAS (en {lang_name(lang)}):"""

    answer = ""
    try:
        from utils.llm import generate as llm_generate
        answer = llm_generate(prompt, json_mode=False, max_retries=1).strip()
    except RuntimeError:
        # Todos los modelos fallaron por cuota
        answer = t_lang("atlas.rate_limited", lang)
    except Exception:
        answer = t_lang("atlas.error", lang)

    if not answer:
        if not chunks:
            answer = t_lang("atlas.no_docs", lang)
        else:
            answer = t_lang("atlas.cant_generate", lang)

    intent_label = intent_context.get("intent") if intent_context else "document_query"

    db.table("chat_messages").insert({
        "employee_id": employee_id,
        "module_id":   module_id,
        "role":        "user",
        "content":     query,
        "intent":      intent_label,
    }).execute()

    db.table("chat_messages").insert({
        "employee_id": employee_id,
        "module_id":   module_id,
        "role":        "assistant",
        "content":     answer,
        "intent":      "response",
    }).execute()

    return answer


def get_history(employee_id: str, module_id: str | None, db) -> list[dict]:
    """Recupera el historial de chat del empleado para un módulo."""
    q = db.table("chat_messages").select("role, content, intent, created_at").eq("employee_id", employee_id)
    if module_id:
        q = q.eq("module_id", module_id)
    return (q.order("created_at").execute().data) or []


def count_questions(employee_id: str, module_id: str, db) -> int:
    """Cuenta cuántas preguntas hizo el empleado sobre un módulo (dato que usa Artemis)."""
    result = (
        db.table("chat_messages")
        .select("id", count="exact")
        .eq("employee_id", employee_id)
        .eq("module_id", module_id)
        .eq("role", "user")
        .execute()
    )
    return result.count or 0


def generate_module_route(company_id: str, db, lang: str = "es") -> list[dict]:
    """
    Analiza los documentos de la empresa y propone una ruta de módulos estructurada.
    Parte del pipeline Atlas + Athena para el onboarding automático.
    """
    import json

    chunks_result = db.table("document_chunks").select("content, document_id").eq("company_id", company_id).limit(80).execute()
    if not chunks_result.data:
        raise ValueError("No hay documentos procesados. Subí documentos primero.")

    doc_result = db.table("documents").select("id, filename").eq("company_id", company_id).eq("processed", True).execute()
    doc_names = {d["id"]: d["filename"] for d in (doc_result.data or [])}

    by_doc: dict[str, list[str]] = {}
    for chunk in chunks_result.data:
        by_doc.setdefault(chunk["document_id"], []).append(chunk["content"])

    sections = []
    for doc_id, chunks in by_doc.items():
        fname = doc_names.get(doc_id, doc_id)
        sections.append(f"=== {fname} ===\n" + "\n".join(chunks[:8]))

    content = "\n\n".join(sections)[:14000]

    prompt = f"""Analizá los siguientes documentos corporativos y generá una ruta de onboarding
estructurada para empleados nuevos durante su período de prueba laboral (60 días).

DOCUMENTOS:
{content}

INSTRUCCIONES:
- Identificá los temas principales que efectivamente aparecen en los documentos
- NO inventes módulos sobre temas que no estén respaldados por contenido real
- Si los documentos hablan de cultura o valores, ese módulo va primero
- Si los documentos son solo técnicos/operativos, empezá por lo más general
- Ordená los módulos de lo más general a lo más específico dentro de lo que hay
- Máximo 6 módulos para el MVP
- Cada módulo debe completarse en 15-30 minutos de lectura
- IMPORTANTE — Los títulos y temas de los módulos deben estar redactados en {lang_name(lang)}.

Respondé ÚNICAMENTE con este JSON (sin texto adicional):
{{
  "modulos": [
    {{
      "orden": 1,
      "titulo": "Título claro y motivador del módulo",
      "tema_principal": "Descripción breve del tema central",
      "documentos_fuente": ["nombre del archivo fuente"],
      "duracion_estimada_minutos": 20
    }}
  ]
}}"""

    from utils.llm import generate as llm_generate
    text = llm_generate(prompt, json_mode=True, max_retries=1)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        text = text.strip()
        s, e = text.find("{"), text.rfind("}") + 1
        data = json.loads(text[s:e])

    modules = data.get("modulos", [])
    if not modules:
        raise RuntimeError("Atlas no pudo generar módulos válidos desde los documentos.")
    return modules


def save_approved_modules(modules: list[dict], company_id: str, db) -> list[str]:
    """Guarda los módulos aprobados por el admin y desactiva los anteriores."""
    db.table("modules").update({"status": "inactive"}).eq("company_id", company_id).execute()

    ids = []
    for mod in modules:
        result = db.table("modules").insert({
            "company_id":       company_id,
            "title":            mod["titulo"],
            "topic":            mod.get("tema_principal", ""),
            "order_index":      mod.get("orden", 0),
            "duration_minutes": mod.get("duracion_estimada_minutos", 20),
            "source_documents": mod.get("documentos_fuente", []),
            "status":           "active",
        }).execute()
        if result.data:
            ids.append(result.data[0]["id"])
    return ids


def get_active_modules(company_id: str, db) -> list[dict]:
    return db.table("modules").select("*").eq("company_id", company_id).eq("status", "active").order("order_index").execute().data or []


def assign_modules_to_employee(employee_id: str, company_id: str, db) -> None:
    """Crea los registros de progreso para cada módulo activo si no existen."""
    for mod in get_active_modules(company_id, db):
        existing = db.table("employee_progress").select("id").eq("employee_id", employee_id).eq("module_id", mod["id"]).execute()
        if not existing.data:
            db.table("employee_progress").insert({
                "employee_id": employee_id,
                "module_id":   mod["id"],
                "status":      "not_started",
            }).execute()
