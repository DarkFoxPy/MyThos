import streamlit as st

st.set_page_config(
    page_title="Mythos",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9881;</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.theme import apply as apply_theme, logo_html
from utils import i18n
from utils.i18n import t
from pages import login, admin, employee, supervisor


def _init():
    i18n.init_lang()
    for key, val in {
        "user": None, "session": None, "profile": None,
        "role": None, "company_id": None, "access_token": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _sidebar():
    apply_theme()
    with st.sidebar:
        st.markdown(logo_html(72), unsafe_allow_html=True)
        st.markdown("""
<div style="margin-top:0.5rem; margin-bottom:1rem; border-bottom:1px solid #1E1E1E; padding-bottom:1rem;">
  <div style="font-size:1rem; font-weight:700; letter-spacing:0.12em; color:#FFFFFF;">MYTHOS</div>
  <div style="font-size:0.68rem; color:#666; letter-spacing:0.1em; text-transform:uppercase; margin-top:2px;">Multi-Agent Intelligence System</div>
</div>
""", unsafe_allow_html=True)

        if st.session_state.user:
            p = st.session_state.profile
            role_key = f"sidebar.role.{st.session_state.role}"
            st.markdown(f"""
<div style="margin-bottom:1rem; padding:0.75rem; background:#0F0F0F; border:1px solid #1E1E1E; border-radius:2px;">
  <div style="font-size:0.85rem; font-weight:600; color:#FFFFFF;">{p.get('full_name','')}</div>
  <div style="font-size:0.72rem; color:#666; text-transform:uppercase; letter-spacing:0.08em; margin-top:2px;">{t(role_key)}</div>
</div>
""", unsafe_allow_html=True)

            st.markdown(f"""
<div style="font-size:0.68rem; color:#666; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.5rem;">{t('sidebar.active_agents')}</div>
""", unsafe_allow_html=True)
            from utils import flags
            badges = """
<div class="agent-badge"><span class="dot dot-green"></span>Athena &mdash; Orchestrator</div>
<div class="agent-badge"><span class="dot dot-green"></span>Atlas &mdash; RAG</div>
<div class="agent-badge"><span class="dot dot-green"></span>Apollo &mdash; NLP</div>
<div class="agent-badge"><span class="dot dot-green"></span>Artemis &mdash; Evaluation</div>
"""
            if flags.is_post_mvp():
                badges += '<div class="agent-badge"><span class="dot dot-green"></span>Quirón &mdash; Capture</div>\n'
            st.markdown(badges, unsafe_allow_html=True)

            st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
            if st.button(t("sidebar.signout"), use_container_width=True):
                lang = st.session_state.get("lang", "es")
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.session_state.lang = lang
                st.rerun()


def main():
    # Atajo de desarrollo invisible: ?modopostMVP=1 en la URL activa el modo
    # post-MVP (muestra Quirón). No aparece en ningún control del front.
    from utils import flags
    if flags.SECRET_CODE in st.query_params:
        flags.set_post_mvp(True)

    _init()
    _sidebar()

    # Selector de idioma arriba a la derecha
    i18n.selector()

    if not st.session_state.user:
        login.show()
        return

    role       = st.session_state.role
    profile    = st.session_state.profile
    company_id = st.session_state.company_id

    if not company_id:
        st.error(t("err.app_no_company"))
        return

    if role == "admin":
        admin.show(profile, company_id)
    elif role == "supervisor":
        supervisor.show(profile, company_id)
    elif role == "employee":
        employee.show(profile, company_id)
    else:
        st.error(f"{t('err.app_no_role')}: {role}")


if __name__ == "__main__":
    main()
