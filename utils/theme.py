import streamlit as st
import base64

_SVG_LOGO = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="ringGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FF8000" stop-opacity="1" />
      <stop offset="100%" stop-color="#CC6600" stop-opacity="1" />
    </radialGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="200" height="200" fill="transparent" rx="4"/>
  <g transform="translate(100, 100)" filter="url(#glow)">
    <path d="M-65,45 A72,72 0 1,1 65,45"
          fill="none" stroke="url(#ringGrad)" stroke-width="10" stroke-linecap="butt" />
    <path d="M-90,45 L-40,45 L-45,60 L-90,60 Z" fill="url(#ringGrad)" />
    <path d="M90,45 L40,45 L45,60 L90,60 Z" fill="url(#ringGrad)" />
    <circle cx="0" cy="-5" r="35" fill="none" stroke="#FF8000" stroke-width="1.5" stroke-dasharray="4,2" opacity="0.6" />
    <circle cx="0" cy="-5" r="25" fill="none" stroke="#FF8000" stroke-width="2" />
    <path d="M-15,-5 Q0,-25 15,-5 Q0,15 -15,-5 Z" fill="url(#ringGrad)" opacity="0.9" />
    <circle cx="0" cy="-5" r="4" fill="#000" />
    <line x1="0" y1="-65" x2="0" y2="-82" stroke="#FF8000" stroke-width="3" />
    <line x1="-50" y1="-45" x2="-62" y2="-55" stroke="#FF8000" stroke-width="2" />
    <line x1="50" y1="-45" x2="62" y2="-55" stroke="#FF8000" stroke-width="2" />
  </g>
  <text x="100" y="185" text-anchor="middle" fill="#FF8000"
        font-family="Palatino, 'Times New Roman', serif" font-size="16" font-weight="bold" letter-spacing="6">M Y T H O S</text>
  <text x="100" y="195" text-anchor="middle" fill="#FF8000"
        font-family="Arial" font-size="5" opacity="0.7" letter-spacing="1">MULTI-AGENT INTELLIGENCE SYSTEM</text>
</svg>"""


def apply():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
}
.stApp {
    background-color: #050505 !important;
    color: #FFFFFF !important;
}
.main .block-container {
    background-color: #050505 !important;
    padding-top: 2rem;
    max-width: 1200px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0A0A0A !important;
    border-right: 1px solid #1E1E1E !important;
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1E1E1E !important;
}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}
h1 { font-size: 2rem !important; }
h2 { font-size: 1.5rem !important; }
h3 { font-size: 1.2rem !important; }
p, li, span, div { color: #CCCCCC; }
.stMarkdown p { color: #CCCCCC; }
caption, .stCaption { color: #666666 !important; font-size: 0.75rem !important; }

/* ── Primary Button ── */
.stButton > button[kind="primary"],
button[data-testid*="primary"] {
    background-color: #FF8000 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1.5rem !important;
    transition: background-color 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #CC6600 !important;
}

/* ── Secondary Button ── */
.stButton > button {
    background-color: #111111 !important;
    color: #FFFFFF !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 2px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    transition: border-color 0.15s ease, background-color 0.15s ease !important;
}
.stButton > button:hover {
    border-color: #FF8000 !important;
    background-color: #1A1A1A !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background-color: #0F0F0F !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 2px !important;
    color: #FFFFFF !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #FF8000 !important;
    box-shadow: 0 0 0 1px #FF8000 !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
    color: #888888 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #0A0A0A !important;
    border-bottom: 1px solid #1E1E1E !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #666666 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.75rem 1.25rem !important;
}
.stTabs [aria-selected="true"] {
    color: #FF8000 !important;
    border-bottom: 2px solid #FF8000 !important;
    background-color: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background-color: #050505 !important;
    padding-top: 1.5rem !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background-color: #0F0F0F !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
    color: #FFFFFF !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
}
.streamlit-expanderContent {
    background-color: #0A0A0A !important;
    border: 1px solid #1E1E1E !important;
    border-top: none !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background-color: #0F0F0F !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
    padding: 1rem !important;
}
[data-testid="metric-container"] label {
    color: #666666 !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
}

/* ── Progress Bar ── */
.stProgress > div > div > div {
    background-color: #FF8000 !important;
}
.stProgress > div > div {
    background-color: #1A1A1A !important;
    border-radius: 0 !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background-color: #0F0F0F !important;
    border: 1px dashed #2A2A2A !important;
    border-radius: 2px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #FF8000 !important;
}

/* ── Containers / Borders ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background-color: #0F0F0F !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
}

/* ── Alerts ── */
.stSuccess > div {
    background-color: #0A1A0A !important;
    border-left: 3px solid #00CC44 !important;
    color: #FFFFFF !important;
}
.stError > div {
    background-color: #1A0A0A !important;
    border-left: 3px solid #FF3300 !important;
    color: #FFFFFF !important;
}
.stWarning > div {
    background-color: #1A1100 !important;
    border-left: 3px solid #FF8000 !important;
    color: #FFFFFF !important;
}
.stInfo > div {
    background-color: #0A0F1A !important;
    border-left: 3px solid #0088FF !important;
    color: #FFFFFF !important;
}

/* ── Code blocks ── */
.stCodeBlock, code {
    background-color: #0F0F0F !important;
    border: 1px solid #1E1E1E !important;
    color: #FF8000 !important;
    font-size: 0.82rem !important;
}

/* ── Chat ── */
[data-testid="stChatMessage"] {
    background-color: #0A0A0A !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #FF8000 !important;
}

/* ── Select box ── */
.stSelectbox [data-baseweb="select"] > div {
    background-color: #0F0F0F !important;
    border-color: #2A2A2A !important;
    color: #FFFFFF !important;
}

/* ── Status dots ── */
.dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
    flex-shrink: 0;
}
.dot-green  { background-color: #00CC44; }
.dot-yellow { background-color: #FF8000; }
.dot-red    { background-color: #FF3300; }
.dot-gray   { background-color: #444444; }
.dot-blue   { background-color: #0088FF; }

/* ── Agent badge ── */
.agent-badge {
    display: inline-flex;
    align-items: center;
    background-color: #111111;
    border: 1px solid #2A2A2A;
    border-radius: 2px;
    padding: 4px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #FF8000;
    margin: 2px 0;
    width: 100%;
}
.agent-badge .dot { margin-right: 8px; }

/* ── Divider ── */
hr { border-color: #1E1E1E !important; }

/* ── Hide form helper text "Press Enter to submit" ── */
[data-testid="InputInstructions"],
[data-testid="stWidgetLabelHelp"],
div[class*="InputInstructions"] {
    display: none !important;
}

/* ── Hide Streamlit auto-nav ── */
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebarNavItems"] { display: none !important; }
section[data-testid="stSidebarNav"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #050505; }
::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #FF8000; }

/* ── Form ── */
[data-testid="stForm"] {
    background-color: #0A0A0A !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
    padding: 1.5rem !important;
}

/* ── Number input buttons ── */
.stNumberInput button {
    background-color: #111111 !important;
    border-color: #2A2A2A !important;
    color: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)


def logo_html(size: int = 80) -> str:
    svg_b64 = base64.b64encode(_SVG_LOGO.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{svg_b64}" width="{size}" height="{size}" style="display:block;" />'


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
<div style="border-bottom: 1px solid #1E1E1E; padding-bottom: 1rem; margin-bottom: 1.5rem;">
  <h1 style="margin:0; font-size:1.6rem; font-weight:700; letter-spacing:-0.02em;">{title}</h1>
  {"<p style='margin:0.3rem 0 0; font-size:0.8rem; color:#666; letter-spacing:0.04em; text-transform:uppercase;'>" + subtitle + "</p>" if subtitle else ""}
</div>
""", unsafe_allow_html=True)


def status_dot(status: str) -> str:
    mapping = {
        "completed":       ("dot-green",  "Completado"),
        "in_progress":     ("dot-yellow", "En progreso"),
        "not_started":     ("dot-gray",   "No iniciado"),
        "verified":        ("dot-green",  "Verificado"),
        "not_verified":    ("dot-yellow", "No verificado"),
        "breach_detected": ("dot-red",    "Brecha detectada"),
        "breach":          ("dot-red",    "Brecha"),
        "stalled":         ("dot-yellow", "Estancado"),
    }
    cls, label = mapping.get(status, ("dot-gray", status))
    return f'<span class="dot {cls}"></span>{label}'


def card(content_fn, *args, **kwargs):
    with st.container(border=True):
        return content_fn(*args, **kwargs)
