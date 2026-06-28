import html
import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database.client import get_client
from agents import artemis, atlas, athena, quiron
from agents.artemis import parse_breach_detail
from utils.theme import page_header
from utils.i18n import t, get_lang
from utils import export


# ────────────────────────────────────────────────────────────────────────────
#  COLORES (alineados con tema McLaren / Mythos)
# ────────────────────────────────────────────────────────────────────────────
COLOR_OK   = "#00CC44"
COLOR_WARN = "#FF8000"
COLOR_BAD  = "#FF3300"
COLOR_NEU  = "#0088FF"
COLOR_BG   = "#0F0F0F"
COLOR_LINE = "#1E1E1E"
COLOR_TEXT = "#E5E5E5"
COLOR_MUTED= "#666"


def _plotly_layout(fig, height=300, title=None):
    """Aplica tema oscuro consistente a cualquier figura Plotly."""
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40 if title else 10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLOR_TEXT, size=11),
        title=dict(text=title, font=dict(size=13, color=COLOR_TEXT)) if title else None,
        xaxis=dict(gridcolor=COLOR_LINE, color=COLOR_MUTED),
        yaxis=dict(gridcolor=COLOR_LINE, color=COLOR_MUTED),
        showlegend=False,
    )
    return fig


# ────────────────────────────────────────────────────────────────────────────
def show(profile: dict, company_id: str):
    page_header(t("sup.title"), t("sup.subtitle"))

    from utils import flags

    labels = [
        t("sup.tab.alerts"),
        t("sup.tab.overview"),
        t("sup.tab.detail"),
    ]
    show_capture = flags.is_post_mvp()
    if show_capture:
        labels.append(t("sup.tab.capture"))

    tabs = st.tabs(labels)

    with tabs[0]:
        _alerts(company_id)
    with tabs[1]:
        _overview(company_id)
    with tabs[2]:
        _detail(company_id)
    if show_capture:
        with tabs[3]:
            _capture(company_id)


def _capture(company_id: str):
    """Quirón — el supervisor le enseña a Mythos su conocimiento del puesto
    mediante una entrevista guiada que se documenta e indexa en el RAG."""
    st.markdown(f"### {t('sup.capture.title')}")
    st.markdown(f"<p style='font-size:0.82rem; color:#888; line-height:1.6;'>{t('sup.capture.intro')}</p>", unsafe_allow_html=True)

    db = get_client(st.session_state.get("access_token"))

    # ── Resultado de una captura recién guardada ─────────────────────────────
    result = st.session_state.get("capture_result")
    if result:
        st.markdown(f"""
<div style="display:flex; align-items:center; gap:0.75rem; padding:1rem; background:#0A1A0A; border:1px solid #1E3E1E; border-radius:4px; margin-bottom:1rem;">
  <span class="dot dot-green"></span>
  <span style="font-size:0.9rem; color:#00CC44;"><strong>{t('sup.capture.saved')} {result['filename']}</strong> — {result['chunks']} {t('sup.capture.fragments')}</span>
</div>
""", unsafe_allow_html=True)
        with st.expander(t("sup.capture.preview")):
            st.markdown(result.get("document_text", ""))
        if st.button(t("sup.capture.new"), type="primary"):
            for k in ("capture_result", "capture_questions", "capture_topic"):
                st.session_state.pop(k, None)
            st.rerun()
        return

    # ── Paso 1: tema + generar preguntas ─────────────────────────────────────
    topic = st.text_input(
        t("sup.capture.topic_label"),
        value=st.session_state.get("capture_topic", ""),
        placeholder=t("sup.capture.topic_ph"),
    )

    if st.button(t("sup.capture.generate"), type="primary"):
        if not topic.strip():
            st.warning(t("sup.capture.need_topic"))
        else:
            with st.spinner(t("sup.capture.generating")):
                try:
                    qs = quiron.generate_questions(topic.strip(), lang=get_lang())
                    st.session_state.capture_questions = qs
                    st.session_state.capture_topic = topic.strip()
                    st.rerun()
                except Exception as e:
                    err = str(e).lower()
                    st.warning(t("sup.capture.quota") if any(k in err for k in ("429", "quota", "cuota", "rate")) else t("sup.capture.error"))

    # ── Paso 2: responder preguntas + enseñar ────────────────────────────────
    questions = st.session_state.get("capture_questions")
    if questions:
        st.markdown("<hr style='border-color:#1E1E1E; margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.78rem; color:#666;'>{t('sup.capture.answers_hint')}</p>", unsafe_allow_html=True)

        answers = []
        for i, q in enumerate(questions):
            st.markdown(f"<p style='font-size:0.88rem; font-weight:600; color:#FFF; margin-bottom:0.3rem;'>{i+1}. {q}</p>", unsafe_allow_html=True)
            a = st.text_area(t("sup.capture.answer_label"), key=f"cap_ans_{i}", height=90, label_visibility="collapsed")
            answers.append({"pregunta": q, "respuesta": a})

        if st.button(t("sup.capture.save"), type="primary", use_container_width=True):
            if not any((a["respuesta"] or "").strip() for a in answers):
                st.warning(t("sup.capture.empty"))
            else:
                with st.spinner(t("sup.capture.saving")):
                    try:
                        res = quiron.capture(st.session_state.capture_topic, answers, company_id, db, lang=get_lang())
                        st.session_state.capture_result = res
                        st.rerun()
                    except Exception as e:
                        err = str(e).lower()
                        st.warning(t("sup.capture.quota") if any(k in err for k in ("429", "quota", "cuota", "rate")) else t("sup.capture.error"))


# ════════════════════════════════════════════════════════════════════════════
#  TAB 1 — ALERTAS DETALLADAS
# ════════════════════════════════════════════════════════════════════════════
def _alerts(company_id: str):
    st.markdown(f"### {t('sup.alerts.title')}")
    st.markdown(f"<p style='font-size:0.78rem; color:#666;'>{t('sup.alerts.desc')}</p>", unsafe_allow_html=True)

    db = get_client(st.session_state.get("access_token"))

    # Traer empleados y mapeo nombre/módulo
    employees = db.table("profiles").select("id, full_name").eq("company_id", company_id).eq("role", "employee").execute().data or []
    emp_name = {e["id"]: e["full_name"] for e in employees}

    modules = db.table("modules").select("id, title").eq("company_id", company_id).eq("status", "active").execute().data or []
    mod_title = {m["id"]: m["title"] for m in modules}

    # Cargar TODOS los análisis de brechas para esta empresa
    breach_rows = db.table("breach_analyses").select("*").in_("module_id", list(mod_title.keys()) or [""]).execute().data or []

    # Filtrar solo los que necesitan atención (breach o not_verified con bajo score)
    alerts = [b for b in breach_rows if b["status"] in ("breach_detected", "not_verified")]
    # También buscar empleados estancados (>3 días sin avance)
    stalled_alerts = athena.get_pending_alerts(company_id, db, lang=get_lang())
    stalled = [a for a in stalled_alerts if a["type"] == "stalled"]

    # ── Resumen rápido arriba ────────────────────────────────────────────────
    n_breach = sum(1 for b in breach_rows if b["status"] == "breach_detected")
    n_notver = sum(1 for b in breach_rows if b["status"] == "not_verified")
    n_stalled = len(stalled)

    c1, c2, c3 = st.columns(3)
    with c1:
        _kpi_card(t("sup.kpi.breaches"), n_breach, COLOR_BAD, t("sup.kpi.breaches_sub"))
    with c2:
        _kpi_card(t("sup.kpi.notver"), n_notver, COLOR_WARN, t("sup.kpi.notver_sub"))
    with c3:
        _kpi_card(t("sup.kpi.stalled"), n_stalled, COLOR_NEU, t("sup.kpi.stalled_sub"))

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    if not alerts and not stalled:
        st.markdown(f"""
<div style="display:flex; align-items:center; gap:0.75rem; padding:1rem; background:#0A1A0A; border:1px solid #1E3E1E; border-radius:4px;">
  <span class="dot dot-green"></span>
  <span style="font-size:0.9rem; color:#00CC44;"><strong>{t('sup.alerts.none')}</strong></span>
</div>
""", unsafe_allow_html=True)
        return

    # Ordenar alertas: brechas primero, luego not_verified, luego estancados
    alerts.sort(key=lambda b: 0 if b["status"] == "breach_detected" else 1)

    # ── Alertas de brechas / no verificadas ──────────────────────────────────
    for b in alerts:
        _alert_card(b, emp_name.get(b["employee_id"], "—"), mod_title.get(b["module_id"], "—"))

    # ── Alertas de estancamiento ─────────────────────────────────────────────
    for a in stalled:
        st.markdown(f"""
<div style="background:#1A1100; border:1px solid {COLOR_WARN}44; border-left:4px solid {COLOR_WARN}; padding:1rem 1.2rem; border-radius:4px; margin-bottom:0.75rem;">
  <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
    <span class="dot dot-yellow"></span>
    <span style="font-size:0.95rem; font-weight:600; color:#FFFFFF;">{a['employee_name']}</span>
    <span style="font-size:0.78rem; color:#888;">  ·  {a['module_title']}</span>
    <span style="margin-left:auto; font-size:0.7rem; color:{COLOR_WARN}; letter-spacing:0.1em; text-transform:uppercase; font-weight:600;">{t('sup.badge.stalled')}</span>
  </div>
  <div style="font-size:0.85rem; color:#CCC; margin-bottom:0.5rem;">{a['message']}</div>
  <div style="font-size:0.8rem; padding:0.6rem 0.8rem; background:#0A0F1A; border-left:3px solid {COLOR_NEU}; border-radius:2px;">
    <strong style="color:#88BBFF;">{t('sup.alerts.action')}:</strong> <span style="color:#CCC;">{a['action']}</span>
  </div>
</div>
""", unsafe_allow_html=True)


def _alert_card(breach_row: dict, employee_name: str, module_title: str):
    """Tarjeta de alerta detallada con brechas específicas, métricas y acción."""
    status = breach_row["status"]
    is_breach = status == "breach_detected"

    accent = COLOR_BAD if is_breach else COLOR_WARN
    bg = "#1A0A0A" if is_breach else "#1A1100"
    label = t("sup.badge.breach") if is_breach else t("sup.badge.notver")
    dot = "dot-red" if is_breach else "dot-yellow"

    detail = parse_breach_detail(breach_row.get("suggested_action", ""))
    razon = breach_row.get("reason", "")
    accion = detail.get("accion_principal", "") or breach_row.get("suggested_action", "")
    brechas = detail.get("brechas", []) or []
    fortalezas = detail.get("fortalezas", []) or []
    metricas = detail.get("metricas", {})
    indicadores = detail.get("indicadores", {})

    # ── Header ───────────────────────────────────────────────────────────────
    brechas_html = ""
    if brechas:
        items = "".join(f'<div style="display:flex;gap:0.5rem;padding:0.2rem 0;font-size:0.83rem;color:#E0CCCC;"><span style="color:{COLOR_BAD};font-weight:700;">×</span><span>{br}</span></div>' for br in brechas)
        brechas_html = f'<div style="margin-top:0.8rem;padding:0.7rem 0.9rem;background:#1A0A0A;border:1px solid #3D1010;border-radius:4px;"><div style="font-size:0.7rem;color:{COLOR_BAD};letter-spacing:0.1em;text-transform:uppercase;font-weight:700;margin-bottom:0.4rem;">⨯ {t("sup.card.not_understood")}</div>{items}</div>'

    fortalezas_html = ""
    if fortalezas:
        items = "".join(f'<div style="display:flex;gap:0.5rem;padding:0.2rem 0;font-size:0.83rem;color:#CCE0CC;"><span style="color:{COLOR_OK};font-weight:700;">✓</span><span>{fo}</span></div>' for fo in fortalezas)
        fortalezas_html = f'<div style="margin-top:0.5rem;padding:0.7rem 0.9rem;background:#0A1A0A;border:1px solid #1E3E1E;border-radius:4px;"><div style="font-size:0.7rem;color:{COLOR_OK};letter-spacing:0.1em;text-transform:uppercase;font-weight:700;margin-bottom:0.4rem;">✓ {t("sup.card.understood")}</div>{items}</div>'

    accion_html = ""
    if accion:
        accion_html = f'<div style="margin-top:0.5rem;padding:0.7rem 0.9rem;background:#0A0F1A;border-left:3px solid {COLOR_NEU};border-radius:4px;"><div style="font-size:0.7rem;color:#88BBFF;letter-spacing:0.1em;text-transform:uppercase;font-weight:700;margin-bottom:0.25rem;">→ {t("sup.card.action_sup")}</div><div style="font-size:0.85rem;color:#DCE6F2;">{accion}</div></div>'

    st.markdown(f"""
<div style="background:{bg}; border:1px solid {accent}44; border-left:4px solid {accent}; padding:1rem 1.2rem; border-radius:4px; margin-bottom:0.25rem;">
  <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
    <span class="dot {dot}"></span>
    <span style="font-size:0.95rem; font-weight:600; color:#FFFFFF;">{employee_name}</span>
    <span style="font-size:0.78rem; color:#888;">  ·  {module_title}</span>
    <span style="margin-left:auto; font-size:0.7rem; color:{accent}; letter-spacing:0.1em; text-transform:uppercase; font-weight:700;">{label}</span>
  </div>
  <div style="font-size:0.85rem; color:#CCC; margin-bottom:0.3rem; line-height:1.5;">{razon}</div>
  {brechas_html}
  {fortalezas_html}
  {accion_html}
</div>
""", unsafe_allow_html=True)

    # ── Métricas con gráficos pequeños ──────────────────────────────────────
    if metricas:
        alert_key = f"alert_{breach_row.get('id', '')}_{breach_row.get('module_id', '')}"
        c1, c2, c3 = st.columns(3)
        with c1:
            _metric_time(metricas, key=alert_key)
        with c2:
            _metric_quiz(metricas, key=alert_key)
        with c3:
            _metric_consultas(metricas, key=alert_key)
    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)


def _metric_time(m: dict, key: str = ""):
    """Mini-gauge de tiempo dedicado vs mínimo."""
    time_spent = m.get("tiempo_dedicado", 0)
    min_time = m.get("tiempo_minimo", 1)
    full = m.get("duracion_estimada", 20)
    ratio = (time_spent / min_time) if min_time else 0
    color = COLOR_OK if ratio >= 1 else (COLOR_WARN if ratio >= 0.5 else COLOR_BAD)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=time_spent,
        number={"suffix": " min", "font": {"size": 26, "color": color}},
        gauge={
            "axis": {"range": [0, max(full, time_spent + 5)], "tickcolor": COLOR_MUTED, "tickfont": {"size": 9}},
            "bar": {"color": color, "thickness": 0.4},
            "bgcolor": COLOR_BG,
            "borderwidth": 1,
            "bordercolor": COLOR_LINE,
            "threshold": {
                "line": {"color": COLOR_WARN, "width": 2},
                "thickness": 0.75,
                "value": min_time,
            },
            "steps": [
                {"range": [0, min_time], "color": "rgba(255, 51, 0, 0.08)"},
                {"range": [min_time, full], "color": "rgba(0, 204, 68, 0.06)"},
            ],
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        height=170,
        margin=dict(l=10, r=10, t=30, b=5),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text=f"{t('sup.metric.time')}<br><span style='font-size:9px;color:#888'>{t('sup.metric.min')}: {min_time} min · {t('sup.metric.est')}: {full} min</span>",
                   font=dict(size=10, color=COLOR_MUTED), x=0.5, y=0.95),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"metric_time_{key}")


def _metric_quiz(m: dict, key: str = ""):
    """Gauge del puntaje del cuestionario."""
    score = m.get("quiz_score_pct", 0)
    color = COLOR_OK if score >= 70 else (COLOR_WARN if score >= 50 else COLOR_BAD)
    correct = m.get("quiz_correct", 0)
    partial = m.get("quiz_partial", 0)
    incorrect = m.get("quiz_incorrect", 0)
    total = m.get("quiz_total", 0)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "%", "font": {"size": 26, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": COLOR_MUTED, "tickfont": {"size": 9}},
            "bar": {"color": color, "thickness": 0.4},
            "bgcolor": COLOR_BG,
            "borderwidth": 1,
            "bordercolor": COLOR_LINE,
            "steps": [
                {"range": [0, 50], "color": "rgba(255, 51, 0, 0.08)"},
                {"range": [50, 70], "color": "rgba(255, 128, 0, 0.08)"},
                {"range": [70, 100], "color": "rgba(0, 204, 68, 0.06)"},
            ],
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        height=170,
        margin=dict(l=10, r=10, t=30, b=5),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text=f"{t('sup.metric.quiz')}<br><span style='font-size:9px;color:#888'>{correct}✓ {partial}~ {incorrect}✗ {t('sup.metric.of')} {total}</span>",
                   font=dict(size=10, color=COLOR_MUTED), x=0.5, y=0.95),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"metric_quiz_{key}")


def _metric_consultas(m: dict, key: str = ""):
    """Indicador grande de consultas al asistente."""
    consultas = m.get("consultas", 0)
    color = COLOR_OK if 3 <= consultas <= 6 else (COLOR_WARN if consultas < 3 else COLOR_NEU)

    fig = go.Figure(go.Indicator(
        mode="number+delta",
        value=consultas,
        number={"font": {"size": 42, "color": color}},
        domain={"x": [0, 1], "y": [0.3, 0.85]},
    ))
    fig.update_layout(
        height=170,
        margin=dict(l=10, r=10, t=30, b=5),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text=f"{t('sup.metric.consultas')}<br><span style='font-size:9px;color:#888'>{t('sup.metric.ideal')}</span>",
                   font=dict(size=10, color=COLOR_MUTED), x=0.5, y=0.95),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"metric_consultas_{key}")


def _kpi_card(title, value, color, sub=""):
    st.markdown(f"""
<div style="background:{COLOR_BG}; border:1px solid {COLOR_LINE}; border-left:4px solid {color}; border-radius:4px; padding:1rem 1.2rem;">
  <div style="font-size:0.7rem; color:#888; letter-spacing:0.1em; text-transform:uppercase; font-weight:600;">{title}</div>
  <div style="font-size:2rem; font-weight:700; color:{color}; line-height:1.1; margin-top:0.2rem;">{value}</div>
  <div style="font-size:0.72rem; color:#666; margin-top:0.2rem;">{sub}</div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  TAB 2 — OVERVIEW CON GRÁFICOS
# ════════════════════════════════════════════════════════════════════════════
def _overview(company_id: str):
    st.markdown(f"### {t('sup.team.title')}")

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button(t("sup.team.refresh"), use_container_width=True):
            st.rerun()

    with st.spinner(t("sup.team.loading")):
        db = get_client(st.session_state.get("access_token"))
        team = artemis.team_dashboard(company_id, db)

    if not team:
        st.info(t("sup.team.empty"))
        return

    # ── KPIs arriba ──────────────────────────────────────────────────────────
    total_emp = len(team)
    avg_pct = sum(e["overall_pct"] for e in team) / total_emp if total_emp else 0
    n_breach = sum(1 for e in team if e["has_breach"])
    n_done = sum(1 for e in team if e["overall_pct"] == 100)

    c1, c2, c3, c4 = st.columns(4)
    with c1: _kpi_card(t("sup.kpi.active"), total_emp, COLOR_NEU)
    with c2: _kpi_card(t("sup.kpi.avg"), f"{int(avg_pct)}%", COLOR_WARN)
    with c3: _kpi_card(t("sup.kpi.with_breach"), n_breach, COLOR_BAD)
    with c4: _kpi_card(t("sup.kpi.done"), n_done, COLOR_OK)

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Charts row ───────────────────────────────────────────────────────────
    col_a, col_b = st.columns([3, 2])
    with col_a:
        _chart_progress_by_employee(team)
    with col_b:
        _chart_diagnosis_distribution(team)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ── Heatmap empleados × módulos ──────────────────────────────────────────
    _chart_heatmap(team)

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Cards expandibles por empleado ───────────────────────────────────────
    st.markdown(f"<div style='font-size:0.85rem; color:#888; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.5rem;'>{t('sup.overview.detail')}</div>", unsafe_allow_html=True)
    for emp in team:
        pct = emp["overall_pct"]
        breach_count = sum(1 for m in emp["modules"] if m["breach_status"] == "breach_detected")
        notver_count = sum(1 for m in emp["modules"] if m["breach_status"] == "not_verified")

        header_color = COLOR_BAD if emp["has_breach"] else (COLOR_OK if pct == 100 else COLOR_WARN)
        header_label = f"⚠ {breach_count} {t('sup.overview.breaches_n')}" if emp["has_breach"] else (f"✓ {t('status.completed')}" if pct == 100 else f"{pct}% {t('sup.team.complete')}")

        with st.expander(f"{emp['full_name']}  ·  {pct}% — {header_label}", expanded=emp["has_breach"]):
            # Barras por módulo
            mods = emp["modules"]
            labels = [m["module_title"][:30] for m in mods]
            time_data = [m["time_spent_minutes"] for m in mods]
            quiz_data = [m["quiz_score_pct"] for m in mods]

            colors_status = []
            for m in mods:
                bs = m["breach_status"]
                if bs == "breach_detected": colors_status.append(COLOR_BAD)
                elif bs == "not_verified":  colors_status.append(COLOR_WARN)
                elif bs == "verified":      colors_status.append(COLOR_OK)
                else:                       colors_status.append("#444")

            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=(t("sup.chart.time_min"), t("sup.chart.quiz_pct")),
                horizontal_spacing=0.28,
            )
            fig.add_trace(go.Bar(
                x=time_data, y=labels, orientation='h',
                marker=dict(color=colors_status), text=time_data, textposition="outside",
                textfont=dict(size=10, color=COLOR_TEXT),
            ), row=1, col=1)
            fig.add_trace(go.Bar(
                x=quiz_data, y=labels, orientation='h',
                marker=dict(color=colors_status), text=[f"{q}%" for q in quiz_data], textposition="outside",
                textfont=dict(size=10, color=COLOR_TEXT),
            ), row=1, col=2)

            fig.update_xaxes(gridcolor=COLOR_LINE, color=COLOR_MUTED, row=1, col=1)
            fig.update_xaxes(gridcolor=COLOR_LINE, color=COLOR_MUTED, range=[0, 105], row=1, col=2)
            # Etiquetas de módulo solo en el gráfico izquierdo; en el derecho se ocultan
            # para que no se pisen con las barras (son los mismos módulos).
            fig.update_yaxes(color=COLOR_MUTED, automargin=True, row=1, col=1)
            fig.update_yaxes(showticklabels=False, row=1, col=2)
            fig.update_annotations(font_size=11, font_color=COLOR_MUTED)
            fig.update_layout(
                height=max(180, 52 * len(mods) + 90),
                margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color=COLOR_TEXT, size=10),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"emp_bars_{emp['employee_id']}")


def _chart_progress_by_employee(team: list):
    names = [e["full_name"] for e in team]
    pcts  = [e["overall_pct"] for e in team]
    colors = [COLOR_BAD if e["has_breach"] else (COLOR_OK if e["overall_pct"] == 100 else COLOR_WARN) for e in team]

    fig = go.Figure(go.Bar(
        x=pcts, y=names, orientation='h',
        marker=dict(color=colors),
        text=[f"{p}%" for p in pcts], textposition="outside",
        textfont=dict(size=11, color=COLOR_TEXT),
    ))
    fig.update_layout(
        height=max(250, 50 * len(team) + 60),
        margin=dict(l=10, r=30, t=40, b=20),
        title=dict(text=t("sup.chart.progress"), font=dict(size=13, color=COLOR_TEXT), x=0, xanchor="left"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLOR_TEXT, size=11),
        xaxis=dict(range=[0, 110], gridcolor=COLOR_LINE, color=COLOR_MUTED, ticksuffix="%"),
        yaxis=dict(color=COLOR_MUTED, automargin=True),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="chart_progress_by_employee")


def _chart_diagnosis_distribution(team: list):
    counts = {"verified": 0, "not_verified": 0, "breach_detected": 0, "pending": 0}
    for emp in team:
        for mod in emp["modules"]:
            s = mod["breach_status"]
            if s in counts:
                counts[s] += 1
            else:
                counts["pending"] += 1

    labels = [t("status.verified"), t("status.not_verified"), t("status.breach"), t("sup.status.pending")]
    values = [counts["verified"], counts["not_verified"], counts["breach_detected"], counts["pending"]]
    colors = [COLOR_OK, COLOR_WARN, COLOR_BAD, "#444"]

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color=COLOR_BG, width=2)),
        textinfo="value",
        textfont=dict(size=14, color=COLOR_TEXT),
        sort=False,
    ))
    total_eval = sum(values) - counts["pending"]
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        title=dict(text=t("sup.chart.diagnosis"), font=dict(size=13, color=COLOR_TEXT), x=0, xanchor="left"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLOR_TEXT, size=11),
        showlegend=True,
        legend=dict(orientation="v", x=1.05, y=0.5, font=dict(size=10, color=COLOR_MUTED)),
        annotations=[dict(
            text=f"<b>{total_eval}</b><br><span style='font-size:9px;color:#888'>{t('sup.chart.evaluated')}</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=18, color=COLOR_TEXT),
        )],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="chart_diagnosis_distribution")


def _chart_heatmap(team: list):
    if not team or not team[0]["modules"]:
        return

    employees = [e["full_name"] for e in team]
    modules = [m["module_title"][:25] for m in team[0]["modules"]]

    # Matrix de valores numéricos para color
    # 4=verified, 3=not_verified, 2=breach, 1=in_progress, 0=not_started
    status_to_val = {"verified": 4, "not_verified": 3, "breach_detected": 2}
    progress_to_val = {"in_progress": 1, "not_started": 0, "completed": 4}

    z = []
    text = []
    for emp in team:
        row_z = []; row_t = []
        for mod in emp["modules"]:
            bs = mod["breach_status"]
            ps = mod["progress_status"]
            if bs in status_to_val:
                v = status_to_val[bs]
                lbl = {"verified": t("status.verified"), "not_verified": t("status.not_verified"), "breach_detected": t("status.breach")}[bs]
            else:
                v = progress_to_val.get(ps, 0)
                lbl = {"in_progress": t("status.in_progress"), "not_started": t("status.not_started"), "completed": t("status.completed")}.get(ps, "—")
            row_z.append(v)
            row_t.append(f"{lbl}<br>{mod['time_spent_minutes']} min · Quiz: {mod['quiz_score_pct']}%")
        z.append(row_z); text.append(row_t)

    # Colorscale: rojo → naranja → amarillo → verde
    colorscale = [
        [0.0,  "#222"],       # not_started (gris oscuro)
        [0.25, "#444"],       # in_progress
        [0.5,  COLOR_BAD],    # breach
        [0.75, COLOR_WARN],   # not_verified
        [1.0,  COLOR_OK],     # verified
    ]

    fig = go.Figure(go.Heatmap(
        z=z, x=modules, y=employees, text=text,
        colorscale=colorscale, zmin=0, zmax=4,
        showscale=False,
        hovertemplate="%{y}<br>%{x}<br>%{text}<extra></extra>",
        xgap=2, ygap=2,
    ))
    fig.update_layout(
        height=max(200, 50 * len(team) + 100),
        margin=dict(l=10, r=10, t=40, b=80),
        title=dict(text=t("sup.chart.heatmap"), font=dict(size=13, color=COLOR_TEXT), x=0, xanchor="left"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLOR_TEXT, size=10),
        xaxis=dict(tickangle=-30, color=COLOR_MUTED, side="bottom"),
        yaxis=dict(color=COLOR_MUTED, automargin=True),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="chart_heatmap")

    # Leyenda manual
    st.markdown(f"""
<div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:-0.5rem; font-size:0.72rem; color:#888;">
  <span><span style="display:inline-block;width:10px;height:10px;background:{COLOR_OK};border-radius:2px;margin-right:5px;"></span>{t('status.verified')}</span>
  <span><span style="display:inline-block;width:10px;height:10px;background:{COLOR_WARN};border-radius:2px;margin-right:5px;"></span>{t('status.not_verified')}</span>
  <span><span style="display:inline-block;width:10px;height:10px;background:{COLOR_BAD};border-radius:2px;margin-right:5px;"></span>{t('status.breach')}</span>
  <span><span style="display:inline-block;width:10px;height:10px;background:#444;border-radius:2px;margin-right:5px;"></span>{t('status.in_progress')}</span>
  <span><span style="display:inline-block;width:10px;height:10px;background:#222;border-radius:2px;margin-right:5px;"></span>{t('status.not_started')}</span>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  TAB 3 — DETALLE POR EMPLEADO
# ════════════════════════════════════════════════════════════════════════════
def _detail(company_id: str):
    db = get_client(st.session_state.get("access_token"))
    employees = db.table("profiles").select("id, full_name").eq("company_id", company_id).eq("role", "employee").execute().data or []

    if not employees:
        st.info(t("sup.detail.empty"))
        return

    options = {e["full_name"]: e["id"] for e in employees}
    selected = st.radio(
        f"{t('sup.detail.employee')}:",
        list(options.keys()),
        horizontal=True,
    )
    emp_id = options[selected]
    modules = atlas.get_active_modules(company_id, db)

    st.markdown(f"### {selected}")

    status_lbls = {"not_started": t("status.not_started"), "in_progress": t("status.in_progress"), "completed": t("status.completed")}
    breach_lbls = {"verified": t("status.verified"), "not_verified": t("status.not_verified"), "breach_detected": t("status.breach")}

    for mod in modules:
        prog     = db.table("employee_progress").select("*").eq("employee_id", emp_id).eq("module_id", mod["id"]).execute().data
        breach   = db.table("breach_analyses").select("*").eq("employee_id", emp_id).eq("module_id", mod["id"]).execute().data
        qresults = db.table("quiz_results").select("score, answer, justification, question_id, created_at").eq("employee_id", emp_id).eq("module_id", mod["id"]).execute().data or []

        # Determinar color y label del módulo en el expander
        if breach:
            bs = breach[0]["status"]
            module_label = {"verified": f"✓ {t('status.verified')}", "not_verified": f"~ {t('status.not_verified')}", "breach_detected": f"✗ {t('status.breach')}"}.get(bs, "")
        else:
            module_label = ""

        with st.expander(f"{t('emp.module')} {mod['order_index']}: {mod['title']}  {('— ' + module_label) if module_label else ''}"):
            if prog:
                p = prog[0]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(t("sup.detail.status"), status_lbls.get(p["status"], p["status"]))
                with col2:
                    st.metric(t("sup.detail.time"), f"{p.get('time_spent_minutes',0)} min")
                with col3:
                    if qresults:
                        total = len(qresults)
                        correct = sum(1 for r in qresults if r["score"] == "correct")
                        partial = sum(1 for r in qresults if r["score"] == "partial")
                        pct = int(((correct + partial * 0.5) / total) * 100)
                        st.metric(t("emp.quiz"), f"{pct}%")

                if qresults:
                    st.markdown(f"""<div style="font-size:0.72rem; color:#666; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.5rem; margin-top:0.75rem;">{t('sup.detail.quiz_detail')}</div>""", unsafe_allow_html=True)
                    # Texto de las preguntas para mostrar contexto junto a cada respuesta
                    qrows = db.table("quiz_questions").select("id, question").eq("module_id", mod["id"]).execute().data or []
                    q_text = {q["id"]: q["question"] for q in qrows}
                    score_dots = {"correct": "dot-green", "partial": "dot-yellow", "incorrect": "dot-red"}
                    for i, r in enumerate(qresults):
                        dc = score_dots.get(r["score"], "dot-gray")
                        question = html.escape(q_text.get(r.get("question_id"), ""))
                        answer = html.escape((r.get("answer") or "").strip()) or "—"
                        st.markdown(f"""
<div style="padding:0.6rem 0.75rem; background:#0F0F0F; border:1px solid #1E1E1E; border-radius:2px; margin-bottom:6px; font-size:0.8rem; color:#CCCCCC;">
  <div style="font-weight:600; color:#FFF; margin-bottom:0.35rem;"><span class="dot {dc}"></span>Q{i+1}{(': ' + question) if question else ''}</div>
  <div style="margin:0.15rem 0 0.4rem; padding:0.45rem 0.6rem; background:#0A0A0A; border-left:3px solid #0088FF; border-radius:2px;">
    <span style="font-size:0.68rem; color:#88BBFF; letter-spacing:0.08em; text-transform:uppercase;">{t('sup.detail.answer')}</span><br>
    <span style="color:#E5E5E5; white-space:pre-wrap;">{answer}</span>
  </div>
  <div style="font-size:0.78rem; color:#999;">{html.escape(r.get('justification') or '')}</div>
</div>
""", unsafe_allow_html=True)

                if breach:
                    b = breach[0]
                    detail = parse_breach_detail(b.get("suggested_action", ""))
                    bdot = {"verified": "dot-green", "not_verified": "dot-yellow", "breach_detected": "dot-red"}.get(b["status"], "dot-gray")

                    st.markdown(f"""
<div style="margin-top:1rem;">
  <div style="font-size:0.72rem; color:#666; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.4rem;">{t('sup.detail.diagnosis')}</div>
  <div style="font-size:0.95rem; color:#FFF; margin-bottom:0.5rem;"><span class="dot {bdot}"></span><strong>{breach_lbls.get(b['status'], b['status'])}</strong></div>
  <div style="font-size:0.85rem; color:#CCC; line-height:1.5; padding:0.5rem 0.8rem; background:#0F0F0F; border-left:3px solid #888; border-radius:2px; margin-bottom:0.6rem;">{b.get('reason','')}</div>
</div>
""", unsafe_allow_html=True)

                    # Métricas con gauges si hay detail estructurado
                    metricas = detail.get("metricas", {})
                    if metricas:
                        detail_key = f"detail_{emp_id}_{mod['id']}"
                        c1, c2, c3 = st.columns(3)
                        with c1: _metric_time(metricas, key=detail_key)
                        with c2: _metric_quiz(metricas, key=detail_key)
                        with c3: _metric_consultas(metricas, key=detail_key)

                    # Brechas específicas
                    brechas = detail.get("brechas", [])
                    if brechas:
                        st.markdown(f"""
<div style="margin-top:0.6rem; padding:0.8rem 1rem; background:#1A0A0A; border:1px solid #3D1010; border-radius:4px;">
  <div style="font-size:0.72rem; color:{COLOR_BAD}; letter-spacing:0.1em; text-transform:uppercase; font-weight:700; margin-bottom:0.5rem;">⨯ {t("sup.card.not_understood")}</div>
""", unsafe_allow_html=True)
                        for br in brechas:
                            st.markdown(f"""<div style="display:flex; gap:0.5rem; padding:0.3rem 0; font-size:0.83rem; color:#E0CCCC;"><span style="color:{COLOR_BAD};">×</span><span>{br}</span></div>""", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # Fortalezas
                    fortalezas = detail.get("fortalezas", [])
                    if fortalezas:
                        st.markdown(f"""
<div style="margin-top:0.5rem; padding:0.8rem 1rem; background:#0A1A0A; border:1px solid #1E3E1E; border-radius:4px;">
  <div style="font-size:0.72rem; color:{COLOR_OK}; letter-spacing:0.1em; text-transform:uppercase; font-weight:700; margin-bottom:0.5rem;">✓ {t("sup.card.understood")}</div>
""", unsafe_allow_html=True)
                        for fo in fortalezas:
                            st.markdown(f"""<div style="display:flex; gap:0.5rem; padding:0.3rem 0; font-size:0.83rem; color:#CCE0CC;"><span style="color:{COLOR_OK};">✓</span><span>{fo}</span></div>""", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # Acción sugerida
                    accion = detail.get("accion_principal", "") or b.get("suggested_action", "")
                    if accion and not (accion.startswith("{") and "accion_principal" in accion):
                        st.markdown(f"""
<div style="margin-top:0.6rem; padding:0.8rem 1rem; background:#0A0F1A; border-left:3px solid {COLOR_NEU}; border-radius:4px;">
  <div style="font-size:0.72rem; color:#88BBFF; letter-spacing:0.1em; text-transform:uppercase; font-weight:700; margin-bottom:0.3rem;">→ {t('sup.detail.suggested')}</div>
  <div style="font-size:0.85rem; color:#DCE6F2;">{accion}</div>
</div>
""", unsafe_allow_html=True)

                elif p and p["status"] == "completed":
                    if st.button(t("sup.detail.analyze"), key=f"analyze_{emp_id}_{mod['id']}"):
                        with st.spinner(t("sup.detail.analyzing")):
                            try:
                                artemis.analyze_breach(emp_id, mod["id"], company_id, db, lang=get_lang())
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.markdown(f"""<span style="font-size:0.78rem; color:#444;">{t('sup.detail.not_started')}</span>""", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1E1E1E; margin:1.5rem 0;'>", unsafe_allow_html=True)
    history = db.table("chat_messages").select("role, content, intent, created_at").eq("employee_id", emp_id).order("created_at").execute().data or []
    if history:
        with st.expander(f"{t('sup.detail.chat_history')} — {selected} ({len(history)} {t('sup.detail.messages')})"):
            for msg in history:
                sender = t("sup.detail.sender_emp") if msg["role"] == "user" else "Atlas"
                dot_cls = "dot-blue" if msg["role"] == "user" else "dot-yellow"
                intent_tag = f" <code style='color:#FF8000; background:transparent; font-size:0.68rem;'>{msg['intent']}</code>" if msg.get("intent") and msg["role"] == "user" else ""
                st.markdown(f"""
<div style="padding:0.5rem 0.75rem; background:#0A0A0A; border:1px solid #1E1E1E; border-radius:2px; margin-bottom:4px;">
  <div style="font-size:0.72rem; color:#555; margin-bottom:0.3rem;"><span class="dot {dot_cls}"></span>{sender}{intent_tag}</div>
  <div style="font-size:0.8rem; color:#CCCCCC;">{msg['content']}</div>
</div>
""", unsafe_allow_html=True)
