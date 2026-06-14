import streamlit as st
from database.client import get_client
from agents import atlas, artemis, athena
from utils.theme import page_header
from utils.i18n import t, get_lang


def show(profile: dict, company_id: str):
    employee_id = profile["id"]
    db = get_client(st.session_state.get("access_token"))

    atlas.assign_modules_to_employee(employee_id, company_id, db)

    page_header(f"{t('emp.welcome')}, {profile['full_name']}", t("emp.subtitle"))

    tab_route, tab_chat = st.tabs([t("emp.tab.route"), t("emp.tab.assistant")])

    with tab_route:
        _route_tab(employee_id, company_id, db)
    with tab_chat:
        _chat_tab(employee_id, company_id, db)


def _route_tab(employee_id: str, company_id: str, db):
    modules = atlas.get_active_modules(company_id, db)
    if not modules:
        st.info(t("emp.route.not_ready"))
        return

    progress = db.table("employee_progress").select("*").eq("employee_id", employee_id).execute().data or []
    prog_map = {p["module_id"]: p for p in progress}

    completed_n = sum(1 for p in prog_map.values() if p["status"] == "completed")
    total       = len(modules)
    pct         = int((completed_n / total) * 100) if total else 0

    st.markdown(f"""
<div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.5rem;">
  <div style="flex:1; height:3px; background:#1A1A1A; border-radius:0; overflow:hidden;">
    <div style="width:{pct}%; height:100%; background:#FF8000; transition:width 0.3s;"></div>
  </div>
  <div style="font-size:0.75rem; color:#FF8000; font-weight:600; white-space:nowrap;">{pct}% &nbsp; {completed_n}/{total} {t('emp.modules')}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    for mod in modules:
        prog   = prog_map.get(mod["id"], {})
        status = prog.get("status", "not_started")
        time_s = prog.get("time_spent_minutes", 0)

        status_dots = {"not_started": "dot-gray", "in_progress": "dot-yellow", "completed": "dot-green"}
        status_lbls = {"not_started": t("status.not_started"), "in_progress": t("status.in_progress"), "completed": t("status.completed")}

        with st.expander(
            f"{t('emp.module')} {mod['order_index']}  ·  {mod['title']}",
            expanded=(status == "in_progress")
        ):
            col_info, col_status = st.columns([3, 1])
            with col_info:
                st.markdown(f"<span style='font-size:0.78rem; color:#888;'>{t('emp.topic')}:</span> <span style='font-size:0.82rem; color:#CCC;'>{mod.get('topic','')}</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size:0.78rem; color:#888;'>{t('emp.estimated')}:</span> <span style='font-size:0.82rem; color:#CCC;'>{mod.get('duration_minutes',20)} min</span>", unsafe_allow_html=True)
                if time_s > 0:
                    st.markdown(f"<span style='font-size:0.75rem; color:#555;'>{t('emp.time_logged')}: {time_s} min</span>", unsafe_allow_html=True)
            with col_status:
                st.markdown(f'<span class="dot {status_dots[status]}"></span>{status_lbls[status]}', unsafe_allow_html=True)

                qsum = artemis.quiz_summary(employee_id, mod["id"], db)
                if qsum["total"] > 0:
                    score = qsum["score_pct"]
                    sc = "dot-green" if score >= 70 else ("dot-yellow" if score >= 50 else "dot-red")
                    st.markdown(f"""<div style="margin-top:0.5rem; font-size:0.75rem; color:#888;">{t('emp.quiz')} <span class="dot {sc}"></span><strong style="color:#FFF;">{score}%</strong></div>""", unsafe_allow_html=True)

                breach = db.table("breach_analyses").select("status, reason").eq("employee_id", employee_id).eq("module_id", mod["id"]).execute().data
                if breach:
                    bstatus = breach[0]["status"]
                    bdot = {"verified": "dot-green", "not_verified": "dot-yellow", "breach_detected": "dot-red"}.get(bstatus, "dot-gray")
                    blbl = {"verified": t("status.verified"), "not_verified": t("status.not_verified"), "breach_detected": t("status.breach")}.get(bstatus, bstatus)
                    st.markdown(f"""<div style="margin-top:0.5rem; font-size:0.72rem; color:#888;">Artemis &nbsp; <span class="dot {bdot}"></span>{blbl}</div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

            if status == "not_started":
                if st.button(t("emp.start_module"), key=f"start_{mod['id']}", type="primary"):
                    db.table("employee_progress").update(
                        {"status": "in_progress", "started_at": "now()"}
                    ).eq("employee_id", employee_id).eq("module_id", mod["id"]).execute()
                    st.rerun()

            elif status == "in_progress":
                col1, col2 = st.columns(2)
                with col1:
                    mins = st.number_input(t("emp.time_spent"), min_value=0, value=time_s, key=f"time_{mod['id']}")
                    if st.button(t("emp.save_time"), key=f"savetime_{mod['id']}"):
                        db.table("employee_progress").update(
                            {"time_spent_minutes": mins}
                        ).eq("employee_id", employee_id).eq("module_id", mod["id"]).execute()
                        st.rerun()
                with col2:
                    if st.button(t("emp.take_quiz"), key=f"quiz_{mod['id']}", type="primary"):
                        st.session_state.quiz_module = mod["id"]
                        st.rerun()

                if st.session_state.get("quiz_module") == mod["id"]:
                    _quiz(employee_id, mod["id"], company_id, db)

            elif status == "completed":
                if st.session_state.get("quiz_module") == mod["id"]:
                    _quiz(employee_id, mod["id"], company_id, db)


def _quiz(employee_id: str, module_id: str, company_id: str, db):
    st.markdown("<hr style='border-color:#1E1E1E; margin:1rem 0;'>", unsafe_allow_html=True)
    st.markdown(f"### {t('emp.quiz.title')}")
    st.markdown(f"<p style='font-size:0.78rem; color:#666;'>{t('emp.quiz.desc')}</p>", unsafe_allow_html=True)

    with st.spinner(t("emp.quiz.generating")):
        try:
            questions = artemis.generate_questions(module_id, company_id, db, lang=get_lang())
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "cuota" in err or "rate" in err:
                st.warning(t("emp.chat.quota"))
            else:
                st.error(t("emp.chat.error"))
            return

    answered = db.table("quiz_results").select("question_id, score, justification").eq("employee_id", employee_id).eq("module_id", module_id).execute().data or []
    answered_map = {r["question_id"]: r for r in answered}
    score_dots = {
        "correct":   ("dot-green",  t("emp.quiz.score.correct")),
        "partial":   ("dot-yellow", t("emp.quiz.score.partial")),
        "incorrect": ("dot-red",    t("emp.quiz.score.incorrect")),
    }

    all_done = True
    for q in questions:
        st.markdown(f"<p style='font-size:0.88rem; font-weight:600; color:#FFF; margin-bottom:0.5rem;'>{q['question']}</p>", unsafe_allow_html=True)
        if q["id"] in answered_map:
            r = answered_map[q["id"]]
            cls, label = score_dots.get(r["score"], ("dot-gray", r["score"]))
            st.markdown(f"""
<div style="padding:0.6rem 0.75rem; background:#0F0F0F; border:1px solid #1E1E1E; border-radius:2px; margin-bottom:0.75rem;">
  <div style="font-size:0.75rem; color:#888; margin-bottom:0.3rem;"><span class="dot {cls}"></span>{label}</div>
  <div style="font-size:0.8rem; color:#CCCCCC;">{r['justification']}</div>
</div>
""", unsafe_allow_html=True)
        else:
            all_done = False
            ans = st.text_area(f"{t('emp.quiz.your_answer')}:", key=f"ans_{q['id']}", height=100)
            if st.button(t("emp.quiz.submit"), key=f"send_{q['id']}", type="primary"):
                if not ans.strip():
                    st.warning(t("emp.quiz.write_first"))
                else:
                    with st.spinner(t("emp.quiz.evaluating")):
                        try:
                            artemis.grade_answer(q["id"], module_id, employee_id, ans, company_id, db, lang=get_lang())
                            st.rerun()
                        except Exception as e:
                            err = str(e).lower()
                            if "429" in err or "quota" in err or "cuota" in err or "rate" in err:
                                st.warning(t("emp.chat.quota"))
                            else:
                                st.error(t("emp.chat.error"))

    if all_done and questions:
        summary = artemis.quiz_summary(employee_id, module_id, db)
        score = summary["score_pct"]
        sc = "dot-green" if score >= 70 else ("dot-yellow" if score >= 50 else "dot-red")
        st.markdown(f"""
<div style="display:flex; align-items:center; gap:0.75rem; margin:1rem 0 0.5rem;">
  <div style="flex:1; height:3px; background:#1A1A1A; overflow:hidden;">
    <div style="width:{score}%; height:100%; background:#FF8000;"></div>
  </div>
  <div style="font-size:0.75rem; color:#FF8000; font-weight:600;"><span class="dot {sc}"></span>{score}%</div>
</div>
""", unsafe_allow_html=True)

        if st.button(t("emp.complete_module"), type="primary"):
            with st.spinner(t("emp.analyzing")):
                try:
                    db.table("employee_progress").update(
                        {"status": "completed", "completed_at": "now()"}
                    ).eq("employee_id", employee_id).eq("module_id", module_id).execute()
                    result = artemis.analyze_breach(employee_id, module_id, company_id, db, lang=get_lang())
                    msgs = {
                        "verified":        t("emp.diag.verified"),
                        "not_verified":    t("emp.diag.not_verified"),
                        "breach_detected": t("emp.diag.breach"),
                    }
                    st.info(msgs.get(result["status"], t("emp.diag.complete")))
                    if "quiz_module" in st.session_state:
                        del st.session_state.quiz_module
                    st.rerun()
                except Exception as e:
                    err = str(e).lower()
                    if "429" in err or "quota" in err or "cuota" in err or "rate" in err:
                        st.warning(t("emp.chat.quota"))
                    else:
                        st.error(t("emp.chat.error"))


def _chat_tab(employee_id: str, company_id: str, db):
    modules     = atlas.get_active_modules(company_id, db)
    mod_options = {t("emp.chat.general"): None}
    mod_options.update({m["title"]: m["id"] for m in modules})

    selected  = st.selectbox(f"{t('emp.chat.related')}:", list(mod_options.keys()))
    module_id = mod_options[selected]

    history = atlas.get_history(employee_id, module_id, db)

    if not history:
        st.markdown(f"""
<div style="padding:0.75rem; background:#0A0A0A; border:1px solid #1E1E1E; border-radius:2px; font-size:0.8rem; color:#666; margin-bottom:1rem;">
  {t('emp.chat.first')}
</div>
""", unsafe_allow_html=True)

    # Notificaciones transitorias del turno anterior (post-rerun)
    flash_warning = st.session_state.pop("_chat_flash_warning", None)
    flash_info    = st.session_state.pop("_chat_flash_info", None)
    flash_error   = st.session_state.pop("_chat_flash_error", None)

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("intent") and msg["role"] == "user":
                st.markdown(f"""<span style="font-size:0.7rem; color:#444; letter-spacing:0.06em;">Apollo → <code style="color:#FF8000; background:transparent;">{msg['intent']}</code></span>""", unsafe_allow_html=True)

    # Mostrar notificaciones del turno anterior (warning/info/error transitorios)
    if flash_warning: st.warning(flash_warning)
    if flash_info:    st.info(flash_info)
    if flash_error:   st.error(flash_error)

    question = st.chat_input(t("emp.chat.input"))

    if question:
        # Procesar SIN renderizar — atlas.generate_response() y athena._save_direct_response()
        # ya guardan los mensajes en chat_messages. Después hacemos st.rerun() para que
        # se incorporen al historial y aparezcan arriba del chat_input.
        with st.spinner(t("emp.chat.processing")):
            try:
                result = athena.route(question, employee_id, company_id, module_id, db, lang=get_lang())

                # Notificaciones transitorias para el próximo render
                if result.get("escalate"):
                    st.session_state["_chat_flash_warning"] = t("emp.chat.escalated")

                if result.get("trigger_quiz") and module_id:
                    st.session_state.quiz_module = module_id
                    st.session_state["_chat_flash_info"] = t("emp.chat.quiz_enabled")

            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "rate" in err.lower() or "exhausted" in err.lower():
                    st.session_state["_chat_flash_warning"] = t("emp.chat.quota")
                else:
                    # NUNCA mostrar el error crudo de la API al usuario
                    st.session_state["_chat_flash_error"] = t("emp.chat.error")

        st.rerun()
