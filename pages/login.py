import requests
import streamlit as st
from config import SUPABASE_URL, SUPABASE_KEY
from utils.theme import logo_html
from utils.i18n import t


def _autocomplete_fix():
    """Marca los inputs con autocomplete correcto para evitar que el navegador
    proponga generar contraseñas o trate el login como un signup.
    Se ejecuta inline en el documento principal vía st.html, por eso usa
    `document` directamente (no window.parent)."""
    st.html("""
<script>
(function() {
  function fix() {
    try {
      var doc = document;
      doc.querySelectorAll('input[type="password"]').forEach(function(i) {
        i.setAttribute('autocomplete', 'current-password');
        i.setAttribute('data-lpignore', 'false');
      });
      doc.querySelectorAll('input[type="text"]').forEach(function(i) {
        var lbl = i.closest('div')?.parentElement?.querySelector('label');
        var txt = (lbl && lbl.textContent) ? lbl.textContent.toLowerCase() : '';
        if (txt.indexOf('correo') !== -1 || txt.indexOf('email') !== -1 || txt.indexOf('e-mail') !== -1) {
          i.setAttribute('autocomplete', 'username');
        }
      });
      doc.querySelectorAll('form').forEach(function(f) {
        f.setAttribute('autocomplete', 'on');
      });
    } catch (e) {}
  }
  fix();
  setTimeout(fix, 200);
  setTimeout(fix, 600);
  setTimeout(fix, 1200);
})();
</script>
""", unsafe_allow_javascript=True)


def show():
    _autocomplete_fix()
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown(f"""
<div style="text-align:center; padding: 2rem 0 1.5rem;">
  <div style="display:flex; justify-content:center; margin-bottom:1rem;">
    {logo_html(100)}
  </div>
  <div style="font-size:1.4rem; font-weight:700; letter-spacing:0.18em; color:#FFFFFF;">MYTHOS</div>
  <div style="font-size:0.7rem; color:#555; letter-spacing:0.12em; text-transform:uppercase; margin-top:4px;">Multi-Agent Intelligence System</div>
</div>
""", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs([t("auth.signin"), t("auth.register")])
        with tab_login:
            _login()
        with tab_register:
            _register()


def _login():
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    with st.form("login_form"):
        email    = st.text_input(t("auth.email"))
        password = st.text_input(t("auth.password"), type="password")
        submit   = st.form_submit_button(t("auth.submit"), use_container_width=True, type="primary")

    if submit:
        if not email or not password:
            st.error(t("auth.fill_all"))
            return
        try:
            response = requests.post(
                f"{SUPABASE_URL}/auth/v1/token",
                params={"grant_type": "password"},
                headers={
                    "apikey":       SUPABASE_KEY,
                    "Content-Type": "application/json",
                },
                json={"email": email, "password": password},
                timeout=15,
            )

            if response.status_code != 200:
                err = response.json() if response.content else {}
                msg = err.get("msg") or err.get("error_description") or err.get("error") or response.text
                code = err.get("error_code") or err.get("code") or ""

                if "invalid" in str(msg).lower() or "credentials" in str(msg).lower():
                    st.error(t("auth.invalid"))
                else:
                    st.error(f"{t('auth.error')}: {msg}")
                    if code:
                        st.caption(f"{t('auth.error_code')}: {code}")
                return

            data         = response.json()
            user         = data.get("user", {})
            access_token = data.get("access_token")
            meta         = user.get("user_metadata") or {}

            profile = {
                "id":         user.get("id"),
                "full_name":  meta.get("full_name") or user.get("email"),
                "role":       meta.get("role", "employee"),
                "company_id": meta.get("company_id"),
            }

            if not profile["company_id"]:
                st.error(t("auth.no_company"))
                return

            # Asegurar que exista una fila en profiles (para que el supervisor
            # pueda verlo en su dashboard). Si no existe, crearla con el token.
            try:
                from database.client import get_client
                db = get_client(access_token)
                existing = db.table("profiles").select("id").eq("id", user.get("id")).execute().data
                if not existing:
                    db.table("profiles").insert({
                        "id":         profile["id"],
                        "company_id": profile["company_id"],
                        "full_name":  profile["full_name"],
                        "role":       profile["role"],
                    }).execute()
            except Exception:
                pass  # Si falla, igual permitimos el login

            st.session_state.user         = user
            st.session_state.session      = data
            st.session_state.profile      = profile
            st.session_state.role         = profile["role"]
            st.session_state.company_id   = profile["company_id"]
            st.session_state.access_token = access_token
            st.rerun()

        except requests.exceptions.RequestException as e:
            st.error(f"{t('auth.network_err')}: {e}")
        except Exception as e:
            st.error(f"{t('auth.error')}: {e}")


def _register():
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
<div style="font-size:0.75rem; color:#666; padding:0.75rem; border:1px solid #1E1E1E; border-radius:2px; margin-bottom:1rem;">
  {t('auth.need_company_id')}
</div>
""", unsafe_allow_html=True)

    with st.form("register_form"):
        full_name    = st.text_input(t("auth.full_name"))
        email        = st.text_input(t("auth.email"))
        password     = st.text_input(t("auth.password"), type="password")
        company_code = st.text_input(t("auth.company_id"))
        submit       = st.form_submit_button(t("auth.create_account"), use_container_width=True, type="primary")

    # Nota informativa sobre el rol asignado por defecto
    st.markdown(f"""
<div style="font-size:0.72rem; color:#666; padding:0.6rem 0.8rem; background:#0A0F1A; border-left:3px solid #0088FF; border-radius:2px; margin-top:0.6rem;">
  {t('auth.role_employee_only')}
</div>
""", unsafe_allow_html=True)

    if submit:
        if not all([full_name, email, password, company_code]):
            st.error(t("auth.fill_all"))
            return
        # Rol fijo: siempre 'employee'. El admin de RRHH es quien promueve roles.
        role = "employee"
        try:
            response = requests.post(
                f"{SUPABASE_URL}/auth/v1/signup",
                headers={
                    "apikey":       SUPABASE_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "email":    email,
                    "password": password,
                    "data": {
                        "full_name":  full_name,
                        "role":       role,
                        "company_id": company_code,
                    },
                },
                timeout=15,
            )

            if response.status_code in (200, 201):
                st.success(t("auth.account_created"))
            else:
                err = response.json() if response.content else {}
                msg = err.get("msg") or err.get("error_description") or response.text
                st.error(f"{t('auth.error')}: {msg}")
        except Exception as e:
            st.error(f"{t('auth.error')}: {e}")
