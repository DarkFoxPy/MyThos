"""
Artemis — Evaluation Engine
ML scoring + comprehension analytics + breach detection.

Genera preguntas de comprensión aplicada (no memorización), califica respuestas
abiertas con justificación, y produce el diagnóstico de brechas cruzando
tiempo + historial de chat + resultado del quiz.
Resuelve las Fallas 2, 3 y 8 del Entregable 1.
"""
import json
import google.generativeai as genai
from config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    MIN_MODULE_TIME_RATIO, BREACH_SCORE_THRESHOLD, VERIFIED_SCORE_THRESHOLD,
)
from agents.atlas import count_questions
from utils.i18n import lang_name

genai.configure(api_key=GEMINI_API_KEY)

# ── Función A: Generación de preguntas aplicadas ──────────────────────────────

QUESTION_PROMPT = """Sos Artemis, el motor de evaluación del sistema Mythos.
Tu tarea es generar exactamente 3 preguntas de evaluación para el siguiente módulo de onboarding.

CONTENIDO DEL MÓDULO:
{module_content}

REQUISITOS ESTRICTOS para las preguntas:
- Deben evaluar COMPRENSIÓN APLICADA, no memorización
- El empleado debe APLICAR o EXPLICAR el concepto, no copiarlo del texto
- Preferí preguntas situacionales: "Si pasa X, ¿qué harías según la política?"
- Deben ser respondibles solo si realmente comprendió el módulo
- Deben ser claras para alguien que recién ingresa a la empresa
- IMPORTANTE — Las preguntas y los criterios deben estar redactados en {response_language}.

Respondé ÚNICAMENTE con este JSON (sin texto adicional):
{{
  "preguntas": [
    {{
      "pregunta": "Texto completo de la pregunta situacional",
      "criterio_evaluacion": "Qué conceptos clave debe mencionar la respuesta correcta"
    }}
  ]
}}"""

# ── Función B: Calificación de respuestas abiertas ────────────────────────────

GRADING_PROMPT = """Sos Artemis, el motor de evaluación del sistema Mythos.
Evaluá la siguiente respuesta de un empleado en su proceso de onboarding.

CONTENIDO DEL MÓDULO (contexto):
{module_content}

PREGUNTA:
{question}

CRITERIO DE EVALUACIÓN:
{criteria}

RESPUESTA DEL EMPLEADO:
{answer}

Evaluá según estos criterios:
1. ¿Demuestra comprensión real o solo repite palabras del documento?
2. ¿La respuesta es coherente con la política/procedimiento de la empresa?
3. ¿Usó sus propias palabras o parece copiado?

IMPORTANTE — La justificación tiene que estar redactada en {response_language}.

Respondé ÚNICAMENTE con este JSON (sin texto adicional):
{{
  "calificacion": "correct|partial|incorrect",
  "justificacion": "Una oración explicando la calificación",
  "comprension_demostrada": true,
  "uso_propias_palabras": true
}}"""

# ── Función C: Análisis de brechas ───────────────────────────────────────────

BREACH_PROMPT = """Sos Artemis, el motor de análisis del sistema Mythos.
Analizá el comportamiento de un empleado durante el módulo de onboarding "{module_title}"
(tema principal: {module_topic}) y determiná si hay evidencia objetiva de comprensión real.

DATOS RECOLECTADOS:
- Tiempo dedicado al módulo: {time_minutes} minutos
- Duración mínima recomendada: {min_time} minutos
- Duración total estimada del módulo: {full_duration} minutos
- Ratio tiempo/mínimo: {time_ratio}
- Preguntas al chatbot sobre este tema: {chat_questions}
- Puntaje del quiz: {score_pct}% ({correct} correctas, {partial} parciales, {incorrect} incorrectas de {total})
- Módulo completado: {completed}

DETALLE DE RESPUESTAS DEL CUESTIONARIO:
{quiz_detail}

Tu tarea es producir un diagnóstico EXPLÍCITO Y DETALLADO sobre el estado de comprensión,
identificando concretamente qué conceptos NO fueron aprendidos cuando corresponda.

IMPORTANTE — Todos los textos deben estar redactados en {response_language}.

Respondé ÚNICAMENTE con este JSON (sin texto adicional):
{{
  "estado": "verified|not_verified|breach_detected",
  "razon": "Una explicación detallada de 2 a 3 oraciones citando los números concretos. Ej: 'Dedicó solo 5 minutos a un módulo de 20 minutos estimados, es decir 4 veces menos del mínimo aceptable. El quiz dio 33% con 2 respuestas incorrectas sobre 3.'",
  "accion_sugerida": "Acción específica que debe tomar el supervisor, mencionando temas y conceptos concretos. Ej: 'Agendar reunión de 30 minutos para revisar los procedimientos de licencias por matrimonio y paternidad, que son los puntos donde demostró menor comprensión.'",
  "brechas_especificas": [
    "Lista concreta de conceptos o temas que el empleado NO demostró comprender (máximo 5 ítems). Basate en las preguntas incorrectas o parciales del cuestionario."
  ],
  "fortalezas": [
    "Lista de aspectos que SÍ demostró comprender (máximo 3 ítems). Basate en respuestas correctas."
  ],
  "indicador_tiempo": "muy_bajo|bajo|aceptable|alto",
  "indicador_consultas": "ninguna|pocas|adecuadas|muchas",
  "indicador_quiz": "deficiente|insuficiente|aceptable|bueno|excelente"
}}

Criterios para el estado:
- "verified": quiz >= {verified_threshold}% Y tiempo >= mínimo Y módulo completado
- "not_verified": completó pero señales de superficialidad (muy rápido, sin preguntas, quiz bajo)
- "breach_detected": quiz < {breach_threshold}% O no completó O tiempo muy inferior al mínimo (menor a la mitad del mínimo)

Criterios para los indicadores:
- indicador_tiempo: "muy_bajo" si tiempo < 50% del mínimo, "bajo" si < 100% del mínimo, "aceptable" si entre 100-150%, "alto" si > 150%
- indicador_consultas: "ninguna" si 0, "pocas" si 1-2, "adecuadas" si 3-6, "muchas" si > 6
- indicador_quiz: "deficiente" si < 30%, "insuficiente" si 30-49%, "aceptable" si 50-69%, "bueno" si 70-84%, "excelente" si >= 85%"""


def _get_module_content(module_id: str, company_id: str, db) -> str:
    mod = db.table("modules").select("title, topic").eq("id", module_id).single().execute().data
    chunks = db.table("document_chunks").select("content").eq("company_id", company_id).limit(15).execute().data or []
    header = f"Módulo: {mod['title']}\nTema: {mod.get('topic','')}\n\n" if mod else ""
    return header + "\n\n".join(c["content"] for c in chunks)


def generate_questions(module_id: str, company_id: str, db, lang: str = "es") -> list[dict]:
    """
    Función A — Genera 3 preguntas aplicadas para el módulo.
    Si ya existen, las retorna directamente (evita duplicados).
    """
    existing = db.table("quiz_questions").select("*").eq("module_id", module_id).execute().data
    if existing:
        return existing

    content = _get_module_content(module_id, company_id, db)
    prompt = QUESTION_PROMPT.format(module_content=content[:8000], response_language=lang_name(lang))

    from utils.llm import generate as llm_generate
    text = llm_generate(prompt, json_mode=True, max_retries=1)

    try:
        raw = json.loads(text).get("preguntas", [])
    except json.JSONDecodeError:
        t2 = text.strip()
        s, e = t2.find("{"), t2.rfind("}") + 1
        raw = json.loads(t2[s:e]).get("preguntas", []) if s >= 0 else []

    saved = []
    for q in raw:
        result = db.table("quiz_questions").insert({
            "module_id":           module_id,
            "question":            q["pregunta"],
            "evaluation_criteria": q.get("criterio_evaluacion", ""),
        }).execute()
        if result.data:
            saved.append(result.data[0])
    return saved


def grade_answer(question_id: str, module_id: str, employee_id: str, answer: str, company_id: str, db, lang: str = "es") -> dict:
    """
    Función B — Califica la respuesta abierta del empleado.
    Retorna la calificación con justificación y la guarda en la BD.
    """
    q = db.table("quiz_questions").select("*").eq("id", question_id).single().execute().data
    if not q:
        raise ValueError(f"Pregunta {question_id} no encontrada.")

    content = _get_module_content(module_id, company_id, db)
    prompt = GRADING_PROMPT.format(
        module_content=content[:6000],
        question=q["question"],
        criteria=q.get("evaluation_criteria", ""),
        answer=answer,
        response_language=lang_name(lang),
    )

    from utils.llm import generate as llm_generate
    grading = {}
    try:
        text = llm_generate(prompt, json_mode=True, max_retries=1)
        try:
            grading = json.loads(text)
        except json.JSONDecodeError:
            t2 = text.strip()
            s, e = t2.find("{"), t2.rfind("}") + 1
            grading = json.loads(t2[s:e]) if s >= 0 else {}
    except RuntimeError:
        # Cuota agotada en todos los modelos: usar fallback determinista
        grading = {
            "calificacion": "partial",
            "justificacion": "Calificación pendiente: el servicio de evaluación automática "
                             "no está disponible en este momento. Tu respuesta fue registrada "
                             "y el supervisor la revisará manualmente.",
            "comprension_demostrada": False,
            "uso_propias_palabras": True,
        }

    score = grading.get("calificacion", "incorrect")
    if score not in {"correct", "partial", "incorrect"}:
        score = "incorrect"

    result = db.table("quiz_results").insert({
        "employee_id":  employee_id,
        "question_id":  question_id,
        "module_id":    module_id,
        "answer":       answer,
        "score":        score,
        "justification": grading.get("justificacion", ""),
    }).execute()

    return {
        "score":        score,
        "justification": grading.get("justificacion", ""),
        "comprension":  grading.get("comprension_demostrada", False),
        "propias_palabras": grading.get("uso_propias_palabras", False),
        "result_id":    result.data[0]["id"] if result.data else None,
    }


def quiz_summary(employee_id: str, module_id: str, db) -> dict:
    """Resumen del quiz de un empleado en un módulo."""
    data = db.table("quiz_results").select("score, justification").eq("employee_id", employee_id).eq("module_id", module_id).execute().data or []
    if not data:
        return {"total": 0, "correct": 0, "partial": 0, "incorrect": 0, "score_pct": 0, "results": []}

    counts = {"correct": 0, "partial": 0, "incorrect": 0}
    for r in data:
        counts[r["score"]] = counts.get(r["score"], 0) + 1

    total = len(data)
    score_pct = int(((counts["correct"] + counts["partial"] * 0.5) / total) * 100)
    return {"total": total, **counts, "score_pct": score_pct, "results": data}


def analyze_breach(employee_id: str, module_id: str, company_id: str, db, lang: str = "es") -> dict:
    """
    Función C — Diagnóstico multi-dimensional de brechas.
    Cruza: tiempo dedicado + preguntas al chat + resultado del quiz.
    Produce análisis explícito con brechas específicas, fortalezas e indicadores.
    Guarda el análisis completo en la BD y lo retorna.
    """
    prog = db.table("employee_progress").select("*").eq("employee_id", employee_id).eq("module_id", module_id).single().execute().data
    mod  = db.table("modules").select("title, topic, duration_minutes").eq("id", module_id).single().execute().data

    if not prog or not mod:
        raise ValueError("No se encontró progreso o módulo.")

    time_spent    = prog.get("time_spent_minutes", 0)
    completed     = prog["status"] == "completed"
    chat_count    = count_questions(employee_id, module_id, db)
    summary       = quiz_summary(employee_id, module_id, db)
    full_duration = mod.get("duration_minutes", 20)
    min_time      = max(3, int(full_duration * MIN_MODULE_TIME_RATIO))
    time_ratio    = round(time_spent / min_time, 2) if min_time > 0 else 0

    # Detalle de las respuestas del quiz para que Artemis identifique brechas específicas
    quiz_results = db.table("quiz_results").select(
        "score, justification, answer, question_id"
    ).eq("employee_id", employee_id).eq("module_id", module_id).execute().data or []

    quiz_questions = db.table("quiz_questions").select(
        "id, question"
    ).eq("module_id", module_id).execute().data or []
    q_map = {q["id"]: q["question"] for q in quiz_questions}

    quiz_detail_lines = []
    for r in quiz_results:
        q_text = q_map.get(r["question_id"], "(pregunta sin texto)")
        quiz_detail_lines.append(
            f"- Pregunta: {q_text}\n"
            f"  Respuesta del empleado: {r.get('answer','(vacío)')}\n"
            f"  Calificación: {r['score']} — {r.get('justification','')}"
        )
    quiz_detail = "\n".join(quiz_detail_lines) if quiz_detail_lines else "(sin respuestas registradas)"

    prompt = BREACH_PROMPT.format(
        module_title=mod["title"],
        module_topic=mod.get("topic", "(sin tema definido)"),
        time_minutes=time_spent,
        min_time=min_time,
        full_duration=full_duration,
        time_ratio=time_ratio,
        chat_questions=chat_count,
        score_pct=summary["score_pct"],
        correct=summary["correct"],
        partial=summary["partial"],
        incorrect=summary["incorrect"],
        total=summary["total"],
        completed="Sí" if completed else "No",
        verified_threshold=VERIFIED_SCORE_THRESHOLD,
        breach_threshold=BREACH_SCORE_THRESHOLD,
        response_language=lang_name(lang),
        quiz_detail=quiz_detail,
    )

    from utils.llm import generate as llm_generate
    analysis = {}
    try:
        text = llm_generate(prompt, json_mode=True, max_retries=1)
        try:
            analysis = json.loads(text)
        except json.JSONDecodeError:
            t2 = text.strip()
            s, e = t2.find("{"), t2.rfind("}") + 1
            analysis = json.loads(t2[s:e]) if s >= 0 else {}
    except RuntimeError:
        # Cuota agotada: el diagnóstico se construye solo con la lógica determinista de abajo
        analysis = {}

    state = analysis.get("estado", "not_verified")
    if state not in {"verified", "not_verified", "breach_detected"}:
        state = "not_verified"

    # Lógica determinista de fallback para asegurar que el estado refleje la realidad
    # incluso si el LLM falla. El tiempo muy bajo SIEMPRE dispara brecha si no fue verificado.
    if state == "verified":
        if time_spent < min_time or summary["score_pct"] < VERIFIED_SCORE_THRESHOLD:
            state = "not_verified"
    if time_spent < (min_time / 2) and completed:
        # Tiempo menor a la mitad del mínimo → siempre brecha
        state = "breach_detected"
    if summary["score_pct"] < BREACH_SCORE_THRESHOLD and summary["total"] > 0:
        state = "breach_detected"

    # Construir reason y acción concretos con datos reales si el LLM no fue específico
    razon = analysis.get("razon", "") or (
        f"Dedicó {time_spent} minutos al módulo de {full_duration} minutos estimados "
        f"(el mínimo aceptable era {min_time} minutos). "
        f"El cuestionario dio {summary['score_pct']}% con "
        f"{summary['correct']} correctas, {summary['partial']} parciales y "
        f"{summary['incorrect']} incorrectas. "
        f"Hizo {chat_count} consultas al asistente."
    )

    accion = analysis.get("accion_sugerida", "") or (
        "Agendar reunión de seguimiento para revisar los conceptos no comprendidos del módulo."
        if state == "breach_detected" else
        ("Conversar con el empleado para confirmar comprensión real." if state == "not_verified" else
         "Sin acción requerida.")
    )

    brechas    = analysis.get("brechas_especificas", []) or []
    fortalezas = analysis.get("fortalezas", []) or []
    ind_tiempo = analysis.get("indicador_tiempo", "")
    ind_consul = analysis.get("indicador_consultas", "")
    ind_quiz   = analysis.get("indicador_quiz", "")

    # Empacar todo el detalle en suggested_action como JSON estructurado
    # para que la UI pueda mostrarlo de manera rica
    detail_payload = {
        "accion_principal":  accion,
        "brechas":           brechas,
        "fortalezas":        fortalezas,
        "metricas": {
            "tiempo_dedicado":    time_spent,
            "tiempo_minimo":      min_time,
            "duracion_estimada":  full_duration,
            "ratio_tiempo":       time_ratio,
            "consultas":          chat_count,
            "quiz_score_pct":     summary["score_pct"],
            "quiz_correct":       summary["correct"],
            "quiz_partial":       summary["partial"],
            "quiz_incorrect":     summary["incorrect"],
            "quiz_total":         summary["total"],
            "completado":         completed,
        },
        "indicadores": {
            "tiempo":    ind_tiempo,
            "consultas": ind_consul,
            "quiz":      ind_quiz,
        },
    }

    suggested_action_str = json.dumps(detail_payload, ensure_ascii=False)

    payload = {
        "employee_id":      employee_id,
        "module_id":        module_id,
        "status":           state,
        "reason":           razon,
        "suggested_action": suggested_action_str,
    }
    existing = db.table("breach_analyses").select("id").eq("employee_id", employee_id).eq("module_id", module_id).execute().data or []
    if existing:
        db.table("breach_analyses").update(payload).eq("id", existing[0]["id"]).execute()
    else:
        db.table("breach_analyses").insert(payload).execute()

    return {
        "status":            state,
        "reason":            razon,
        "suggested_action":  accion,
        "brechas":           brechas,
        "fortalezas":        fortalezas,
        "indicadores":       detail_payload["indicadores"],
        "metricas":          detail_payload["metricas"],
        "time_spent":        time_spent,
        "min_time":          min_time,
        "chat_questions":    chat_count,
        "quiz_score_pct":    summary["score_pct"],
    }


def parse_breach_detail(suggested_action: str) -> dict:
    """Parsea el JSON estructurado almacenado en suggested_action.
    Devuelve dict vacío si no es JSON parseable (formato viejo)."""
    if not suggested_action:
        return {}
    try:
        data = json.loads(suggested_action)
        if isinstance(data, dict) and "accion_principal" in data:
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return {}


def team_dashboard(company_id: str, db) -> list[dict]:
    """
    Dashboard completo del supervisor con estado de todos los empleados.
    Ordenado por: brechas primero, luego por menor progreso.
    """
    employees = db.table("profiles").select("id, full_name").eq("company_id", company_id).eq("role", "employee").execute().data or []
    modules   = db.table("modules").select("id, title, order_index").eq("company_id", company_id).eq("status", "active").order("order_index").execute().data or []

    if not employees or not modules:
        return []

    result = []
    for emp in employees:
        emp_row = {"employee_id": emp["id"], "full_name": emp["full_name"], "modules": []}

        for mod in modules:
            prog   = db.table("employee_progress").select("status, time_spent_minutes").eq("employee_id", emp["id"]).eq("module_id", mod["id"]).execute().data
            breach = db.table("breach_analyses").select("status, reason, suggested_action").eq("employee_id", emp["id"]).eq("module_id", mod["id"]).execute().data
            qsumm  = quiz_summary(emp["id"], mod["id"], db)

            p_status   = prog[0]["status"]              if prog   else "not_started"
            time_spent = prog[0].get("time_spent_minutes", 0) if prog else 0
            b_status   = breach[0]["status"]            if breach else None
            b_reason   = breach[0]["reason"]            if breach else None
            b_action   = breach[0]["suggested_action"]  if breach else None

            emp_row["modules"].append({
                "module_id":           mod["id"],
                "module_title":        mod["title"],
                "progress_status":     p_status,
                "time_spent_minutes":  time_spent,
                "quiz_score_pct":      qsumm["score_pct"],
                "breach_status":       b_status,
                "breach_reason":       b_reason,
                "suggested_action":    b_action,
            })

        total     = len(modules)
        completed = sum(1 for m in emp_row["modules"] if m["progress_status"] == "completed")
        emp_row["overall_pct"]  = int((completed / total) * 100) if total else 0
        emp_row["has_breach"]   = any(m["breach_status"] == "breach_detected" for m in emp_row["modules"])
        result.append(emp_row)

    result.sort(key=lambda x: (not x["has_breach"], -x["overall_pct"]))
    return result
