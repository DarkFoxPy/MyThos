import uuid
import streamlit as st
from database.client import get_client
from agents import atlas
from utils.processor import process_document
from utils.theme import page_header
from utils.i18n import t, get_lang
from utils import export


def show(profile: dict, company_id: str):
    page_header(t("admin.title"), t("admin.subtitle"))

    tab_docs, tab_route, tab_company = st.tabs([
        t("admin.tab.docs"),
        t("admin.tab.route"),
        t("admin.tab.company"),
    ])

    with tab_docs:
        _documents(company_id)
    with tab_route:
        _route(company_id)
    with tab_company:
        _company(company_id)


def _documents(company_id: str):
    st.markdown(f"### {t('admin.docs.title')}")
    st.markdown(f"<p style='font-size:0.82rem; color:#888;'>{t('admin.docs.desc')}</p>", unsafe_allow_html=True)

    uploaded = st.file_uploader("PDF / DOCX", type=["pdf", "docx"], accept_multiple_files=True)

    if uploaded and st.button(t("admin.docs.process"), type="primary"):
        db = get_client(st.session_state.get("access_token"))
        for f in uploaded:
            with st.spinner(f"{t('admin.docs.indexing')} {f.name}..."):
                try:
                    doc_id = str(uuid.uuid4())
                    db.table("documents").insert({
                        "id": doc_id, "company_id": company_id,
                        "filename": f.name,
                        "storage_path": f"docs/{company_id}/{doc_id}_{f.name}",
                        "processed": False,
                    }).execute()
                    n = process_document(f.read(), f.name, doc_id, company_id, db)
                    st.success(f"{f.name} — {n} {t('admin.docs.fragments')}.")
                except Exception as e:
                    st.error(f"{f.name}: {e}")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""<div style="font-size:0.72rem; color:#666; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.75rem;">{t('admin.docs.indexed')}</div>""", unsafe_allow_html=True)

    db = get_client(st.session_state.get("access_token"))
    docs = db.table("documents").select("id, filename, processed, created_at").eq("company_id", company_id).order("created_at", desc=True).execute().data or []
    if docs:
        for d in docs:
            dot = "🟢" if d["processed"] else "🟡"
            label = t("admin.docs.processed") if d["processed"] else t("admin.docs.pending")
            with st.expander(f"{dot}  {d['filename']}  ·  {label}"):
                if d["processed"]:
                    text = atlas.get_document_text(d["id"], db)
                    if text:
                        st.download_button(
                            t("doc.download"),
                            data=export.text_to_docx_bytes(d["filename"], text),
                            file_name=export.docx_filename(d["filename"]),
                            mime=export.DOCX_MIME,
                            key=f"dl_adm_{d['id']}",
                        )
                        st.markdown(
                            f"<div style='font-size:0.85rem; color:#CCC; line-height:1.6; "
                            f"max-height:480px; overflow-y:auto; white-space:pre-wrap; "
                            f"padding:0.5rem 0.25rem;'>{text}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("—")
                else:
                    st.caption(label)
    else:
        st.info(t("admin.docs.empty"))


def _route(company_id: str):
    st.markdown(f"### {t('admin.route.title')}")
    st.markdown(f"<p style='font-size:0.82rem; color:#888;'>{t('admin.route.desc')}</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button(t("admin.route.generate"), type="primary", use_container_width=True):
            with st.spinner(t("admin.route.analyzing")):
                try:
                    db = get_client(st.session_state.get("access_token"))
                    modules = atlas.generate_module_route(company_id, db, lang=get_lang())
                    st.session_state.proposed_modules = modules
                    st.success(f"{len(modules)} {t('admin.route.proposed')}")
                except Exception as e:
                    err = str(e).lower()
                    if "429" in err or "quota" in err or "cuota" in err or "rate" in err:
                        st.warning(t("emp.chat.quota"))
                    else:
                        st.error(t("emp.chat.error"))

    if st.session_state.get("proposed_modules"):
        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"""<div style="font-size:0.72rem; color:#666; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.75rem;">{t('admin.route.proposal')}</div>""", unsafe_allow_html=True)
        edited = []
        for i, mod in enumerate(st.session_state.proposed_modules):
            with st.expander(f"{t('admin.route.module_n')} {mod.get('orden', i+1)}: {mod.get('titulo','')}", expanded=True):
                title    = st.text_input(t("admin.route.title_label"), value=mod.get("titulo",""), key=f"t{i}")
                topic    = st.text_input(t("admin.route.topic"), value=mod.get("tema_principal",""), key=f"tp{i}")
                duration = st.number_input(t("admin.route.duration"), value=mod.get("duracion_estimada_minutos",20), min_value=5, max_value=120, key=f"d{i}")
                edited.append({
                    "orden": mod.get("orden", i+1),
                    "titulo": title,
                    "tema_principal": topic,
                    "duracion_estimada_minutos": duration,
                    "documentos_fuente": mod.get("documentos_fuente", []),
                })

        with col2:
            if st.button(t("admin.route.approve"), type="primary", use_container_width=True):
                with st.spinner(t("admin.route.activating")):
                    try:
                        db = get_client(st.session_state.get("access_token"))
                        ids = atlas.save_approved_modules(edited, company_id, db)
                        del st.session_state.proposed_modules
                        st.success(f"{t('admin.route.active_route')} {len(ids)} {t('admin.route.modules')}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""<div style="font-size:0.72rem; color:#666; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.75rem;">{t('admin.route.active')}</div>""", unsafe_allow_html=True)
    db = get_client(st.session_state.get("access_token"))
    active = atlas.get_active_modules(company_id, db)
    if active:
        for m in active:
            st.markdown(f"""
<div style="display:flex; align-items:center; padding:0.6rem 0.75rem; background:#0F0F0F; border:1px solid #1E1E1E; border-radius:2px; margin-bottom:4px;">
  <span style="font-size:0.75rem; color:#FF8000; font-weight:700; width:1.5rem;">{m['order_index']}</span>
  <span style="font-size:0.82rem; color:#FFFFFF; flex:1; font-weight:500;">{m['title']}</span>
  <span style="font-size:0.72rem; color:#555;">{m.get('topic','')} &nbsp;&middot;&nbsp; {m.get('duration_minutes',20)} min</span>
</div>
""", unsafe_allow_html=True)
    else:
        st.info(t("admin.route.no_active"))


def _company(company_id: str):
    st.markdown(f"### {t('admin.company.title')}")

    st.markdown(f"""<div style="font-size:0.72rem; color:#666; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.5rem;">{t('admin.company.id_label')}</div>""", unsafe_allow_html=True)
    st.code(company_id)
    st.markdown(f"""<p style="font-size:0.78rem; color:#666; margin-top:0.25rem;">{t('admin.company.id_desc')}</p>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem; border-top:1px solid #1E1E1E; margin-top:1rem;'></div>", unsafe_allow_html=True)

    db = get_client(st.session_state.get("access_token"))
    users = db.table("profiles").select("id, full_name, role, created_at").eq("company_id", company_id).order("created_at", desc=True).execute().data or []

    if not users:
        return

    st.markdown(f"""<div style="font-size:0.72rem; color:#666; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.75rem;">{t('admin.company.users')}</div>""", unsafe_allow_html=True)
    st.markdown(f"""<p style="font-size:0.78rem; color:#666; margin-bottom:1rem;">{t('admin.company.roles_help')}</p>""", unsafe_allow_html=True)

    role_colors = {"admin": "#FF8000", "supervisor": "#0088FF", "employee": "#00CC44"}
    role_options = ["employee", "supervisor", "admin"]
    current_user_id = st.session_state.user.get("id") if st.session_state.get("user") else None

    for u in users:
        is_self = (u["id"] == current_user_id)
        color = role_colors.get(u["role"], "#666")

        cols = st.columns([3, 2, 2, 1])
        with cols[0]:
            st.markdown(f"""
<div style="padding:0.5rem 0; font-size:0.85rem; color:#FFFFFF;">
  {u['full_name']}{' <span style="font-size:0.7rem; color:#888;">(vos)</span>' if is_self else ''}
</div>
""", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""
<div style="padding:0.5rem 0;">
  <span style="font-size:0.7rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:{color}; background:{color}18; padding:3px 9px; border-radius:2px;">
    {t('role.' + u['role'])}
  </span>
</div>
""", unsafe_allow_html=True)
        with cols[2]:
            new_role = st.selectbox(
                "rol",
                role_options,
                index=role_options.index(u["role"]) if u["role"] in role_options else 0,
                format_func=lambda r: t(f"role.{r}"),
                key=f"role_select_{u['id']}",
                label_visibility="collapsed",
                disabled=is_self,
            )
        with cols[3]:
            if not is_self and new_role != u["role"]:
                if st.button(t("admin.company.save_role"), key=f"save_{u['id']}", type="primary", use_container_width=True):
                    try:
                        _update_user_role(db, u["id"], new_role)
                        st.success(f"{u['full_name']} → {t('role.' + new_role)}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


def _update_user_role(db, user_id: str, new_role: str):
    """Actualiza el rol de un usuario en profiles Y en auth.users.raw_user_meta_data
    para que el JWT del usuario refleje el cambio en su próximo login."""
    # 1) Actualizar la tabla profiles
    db.table("profiles").update({"role": new_role}).eq("id", user_id).execute()

    # 2) Actualizar raw_user_meta_data via Auth Admin API (requiere service role key,
    #    pero la anon key igualmente puede invocar RPC si lo permitimos).
    #    Como fallback simple, dejamos solo profiles actualizado. El usuario verá el
    #    nuevo rol al refrescar su sesión (logout/login).
    try:
        import requests
        from config import SUPABASE_URL, SUPABASE_KEY
        token = st.session_state.get("access_token", "")
        requests.put(
            f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"user_metadata": {"role": new_role}},
            timeout=10,
        )
    except Exception:
        # Si la API admin no está accesible con anon key, profiles queda actualizado.
        # El usuario verá el nuevo rol al cerrar sesión e iniciar sesión nuevamente.
        pass
