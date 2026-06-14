"""
Athena — Orchestrator / Agent Controller
LLM + routing + session management.

Recibe cada acción del usuario y decide qué agente debe manejarla.
Gestiona el flujo de la ruta de onboarding y escala al supervisor cuando corresponde.
"""
from agents import apollo, atlas, artemis
from utils.i18n import t_lang


def route(message: str, employee_id: str, company_id: str, module_id: str | None, db, lang: str = "es") -> dict:
    """
    Punto de entrada central del sistema.
    Athena coordina Apollo → Atlas/Artemis y retorna la respuesta al frontend.
    """
    parsed = apollo.parse(message, lang=lang)
    intent = parsed["intent"]

    # Señal de dificultad → Atlas responde Y se escala al supervisor
    if apollo.is_difficulty_signal(parsed):
        query = apollo.get_search_query(parsed)
        history = atlas.get_history(employee_id, module_id, db)
        response = atlas.generate_response(query, company_id, employee_id, module_id, db, history, parsed, lang=lang)
        return {
            "response": response,
            "intent": intent,
            "agent": "Atlas + Athena",
            "escalate": True,
            "trigger_quiz": False,
            "escalate_reason": f"El empleado expresó dificultad: '{message[:80]}'",
        }

    # Señal de módulo completado → Athena activa el quiz de Artemis
    if apollo.is_module_complete(parsed) and module_id:
        msg = t_lang("athena.module_done", lang)
        _save_direct_response(message, msg, employee_id, module_id, intent, db)
        return {
            "response": msg,
            "intent": intent,
            "agent": "Athena",
            "escalate": False,
            "trigger_quiz": True,
        }

    # Saludo o fuera de dominio → Athena responde directamente
    if intent in ("greeting", "out_of_domain"):
        msg = t_lang("athena.greeting" if intent == "greeting" else "athena.out_of_domain", lang)
        _save_direct_response(message, msg, employee_id, module_id, intent, db)
        return {"response": msg, "intent": intent, "agent": "Athena", "escalate": False, "trigger_quiz": False}

    # Consulta de progreso → Athena consulta la BD y responde
    if intent == "progress_check":
        response = _generate_progress_response(employee_id, company_id, db, lang)
        _save_direct_response(message, response, employee_id, module_id, intent, db)
        return {"response": response, "intent": intent, "agent": "Athena", "escalate": False, "trigger_quiz": False}

    # Caso default: document_query → Atlas con Apollo como preprocessor
    query = apollo.get_search_query(parsed)
    history = atlas.get_history(employee_id, module_id, db)
    response = atlas.generate_response(query, company_id, employee_id, module_id, db, history, parsed, lang=lang)
    return {
        "response": response,
        "intent": intent,
        "agent": "Atlas",
        "escalate": False,
        "trigger_quiz": False,
    }


def _save_direct_response(user_msg: str, assistant_msg: str, employee_id: str, module_id: str | None, intent: str, db) -> None:
    db.table("chat_messages").insert({"employee_id": employee_id, "module_id": module_id, "role": "user", "content": user_msg, "intent": intent}).execute()
    db.table("chat_messages").insert({"employee_id": employee_id, "module_id": module_id, "role": "assistant", "content": assistant_msg, "intent": "response"}).execute()


def _generate_progress_response(employee_id: str, company_id: str, db, lang: str = "es") -> str:
    modules  = atlas.get_active_modules(company_id, db)
    progress = db.table("employee_progress").select("module_id, status").eq("employee_id", employee_id).execute().data or []
    prog_map = {p["module_id"]: p["status"] for p in progress}

    title       = t_lang("athena.progress.title", lang)
    module_word = t_lang("athena.progress.module", lang)
    summary_pct = t_lang("athena.progress.summary", lang)
    modules_w   = t_lang("athena.progress.modules", lang)

    lines = []
    for mod in modules:
        status = prog_map.get(mod["id"], "not_started")
        slabel = t_lang(f"athena.progress.status.{status}", lang)
        lines.append(f"- [{slabel}] {module_word} {mod['order_index']}: {mod['title']}")

    completed = sum(1 for s in prog_map.values() if s == "completed")
    total     = len(modules)
    pct       = int((completed / total) * 100) if total else 0

    return f"**{title}:**\n\n" + "\n".join(lines) + f"\n\n**{pct}% {summary_pct}** ({completed}/{total} {modules_w})"


# ── Gestión de alertas ────────────────────────────────────────────────────────

def get_pending_alerts(company_id: str, db, lang: str = "es") -> list[dict]:
    """Empleados con brechas detectadas o estancados >3 días."""
    import datetime
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=3)).isoformat()

    stalled = (
        db.table("employee_progress")
        .select("employee_id, module_id, status, started_at")
        .eq("status", "in_progress").lt("started_at", cutoff).execute().data or []
    )
    breaches = (
        db.table("breach_analyses")
        .select("employee_id, module_id, reason, suggested_action")
        .eq("status", "breach_detected").execute().data or []
    )

    emp_ids = list({r["employee_id"] for r in stalled + breaches})
    if not emp_ids:
        return []

    profiles = db.table("profiles").select("id, full_name").in_("id", emp_ids).execute().data or []
    name_map = {p["id"]: p["full_name"] for p in profiles}
    mod_ids  = list({r["module_id"] for r in stalled + breaches})
    mods     = db.table("modules").select("id, title").in_("id", mod_ids).execute().data or []
    mod_map  = {m["id"]: m["title"] for m in mods}

    alerts = []
    for r in stalled:
        alerts.append({
            "type":          "stalled",
            "employee_name": name_map.get(r["employee_id"], r["employee_id"]),
            "module_title":  mod_map.get(r["module_id"], r["module_id"]),
            "message":       t_lang("alert.stalled.msg", lang),
            "action":        t_lang("alert.stalled.act", lang),
        })
    for r in breaches:
        alerts.append({
            "type":          "breach",
            "employee_name": name_map.get(r["employee_id"], r["employee_id"]),
            "module_title":  mod_map.get(r["module_id"], r["module_id"]),
            "message":       r.get("reason") or t_lang("alert.breach.msg", lang),
            "action":        r.get("suggested_action") or t_lang("alert.breach.act", lang),
        })
    return alerts
