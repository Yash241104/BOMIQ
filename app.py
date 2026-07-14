import io
import time

import streamlit as st
import pandas as pd

from bom_interpreter import generate_engineering_bom
from search_engine import search_bom
from mapping import standardize_bom
from digikey_api import get_api_stats


try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_pdf_bytes(
        df: pd.DataFrame,
        dashboard: dict,
        distributor: str = "DigiKey",
        title: str = "BOMIQ — Final Procurement BOM"
    ) -> bytes:
    """Render a dataframe as a landscape PDF table and return raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=8,
        rightMargin=8,
        topMargin=10,
        bottomMargin=10
    )
    from datetime import datetime

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<font size=20><b>BOMIQ</b></font>",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "<font size=14><b>Final Procurement BOM Report</b></font>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 12))

    report_info = f"""
    <b>Generated :</b> {datetime.now().strftime('%d %b %Y %I:%M %p')}<br/>
    <b>Distributor :</b> {distributor}<br/>
    <b>Total Components :</b> {dashboard['Total Parts']}<br/>
    <b>Components Found :</b> {dashboard['Found']}<br/>
    <b>Automation :</b> {dashboard['Automation']}%<br/>
    <b>Total BOM Cost :</b> ₹{dashboard['Actual Cost']:,.2f}
    """

    elements.append(
        Paragraph(
            report_info,
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))

    if dashboard.get("Target Cost") is not None:

        comparison = f"""
        <b>Target Cost :</b> ₹{dashboard['Target Cost']:,.2f}<br/>
        <b>Difference :</b> ₹{dashboard['Difference']:,.2f}<br/>
        <b>Difference % :</b> {dashboard['Difference %']:.2f}%
        """

        elements.append(
            Paragraph(
                comparison,
                styles["Normal"]
            )
        )

        elements.append(Spacer(1, 16))

    # Columns that don't make sense in a PDF
    columns_to_remove = [
        "Product URL",
        "Remarks"
    ]

    pdf_df = df.drop(
        columns=[c for c in columns_to_remove if c in df.columns],
        errors="ignore"
    )

    table_data = [list(pdf_df.columns)] + pdf_df.astype(str).values.tolist()
    page_width = landscape(A4)[0] - 16

    col_widths = [
        page_width * 0.06,   # Designator
        page_width * 0.08,   # Part Type
        page_width * 0.06,   # Value
        page_width * 0.12,   # Manufacturer
        page_width * 0.16,   # Manufacturer Part Number
        page_width * 0.16,   # DigiKey Part Number
        page_width * 0.08,   # Stock
        page_width * 0.07,   # Unit Price
        page_width * 0.08,   # Total Cost
        page_width * 0.07,   # Validation
        page_width * 0.06    # Status
    ]

    table = Table(
        table_data,
        repeatRows=1,
        colWidths=col_widths
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3B82F6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0,0), (-1,-1), 5.8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("LEFTPADDING", (0,0), (-1,-1), 2),
        ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="BOMIQ | Smart BOM Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# SESSION STATE  (unchanged keys / defaults)
# ==========================================================

if "engineering_bom" not in st.session_state:
    st.session_state.engineering_bom = None

if "search_results" not in st.session_state:
    st.session_state.search_results = None

if "target_cost" not in st.session_state:
    st.session_state.target_cost = 0.0

if "enable_cost_comparison" not in st.session_state:
    st.session_state.enable_cost_comparison = False

if "search_duration" not in st.session_state:
    st.session_state.search_duration = None

if "enable_cost_comparison" not in st.session_state:
    st.session_state.enable_cost_comparison = False

if "api_stats" not in st.session_state:
    st.session_state.api_stats = {
        "connected": False,
        "daily_limit": None,
        "daily_remaining": None,
        "session_calls": 0
    }

if "search_completed" not in st.session_state:
    st.session_state.search_completed = False

# ==========================================================
# ICONS  (lightweight inline Lucide-style SVGs)
# ==========================================================

ICONS = {
    "logo": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z"/></svg>',
    "upload": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    "cpu": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/></svg>',
    "target": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "search": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "check": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "x": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    "download": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    "layers": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "package": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" y1="22" x2="12" y2="12"/></svg>',
    "alert": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "bot": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>',
    "settings": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
}


def icon(name):
    return ICONS.get(name, "")


def render_html(html: str):
    """
    Safely render an HTML string with st.markdown().

    Streamlit's Markdown parser treats any line indented by 4+ spaces
    (and separated from other content by a blank line) as an indented
    code block. HTML built from f-strings inside nested Python `with`
    blocks inherits that source-file indentation, so it can silently
    get rendered as a literal code block instead of live HTML.

    Since whitespace is not meaningful in HTML, this strips every
    line down to its content and drops blank lines before handing the
    string to st.markdown(), which guarantees it can never be
    mistaken for an indented code block.
    """
    cleaned = "\n".join(
        line.strip() for line in html.strip().splitlines() if line.strip() != ""
    )
    st.markdown(cleaned, unsafe_allow_html=True)


# ==========================================================
# GLOBAL CSS  — enterprise dark theme
# ==========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

:root {
    --bg:            #0A0B0F;
    --surface:       #14161C;
    --surface-2:     #1B1E26;
    --border:        #262A34;
    --text:          #E6E8EC;
    --text-dim:      #8B90A0;
    --blue:          #3B82F6;
    --blue-glow:     rgba(59,130,246,0.35);
    --emerald:       #10B981;
    --amber:         #F59E0B;
    --red:           #EF4444;
}

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(59,130,246,0.08), transparent 40%),
        radial-gradient(circle at 85% 15%, rgba(16,185,129,0.06), transparent 35%),
        var(--bg);
}

#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

/* ---------- Section fade-in ---------- */
@keyframes fadeInUp {
    from {opacity: 0; transform: translateY(8px);}
    to {opacity: 1; transform: translateY(0);}
}
.bomiq-section {animation: fadeInUp 0.45s ease-out;}

/* ---------- App navbar (top header) — neon enterprise style ---------- */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;800&display=swap');

.bomiq-navbar {
    position: sticky; top: 0; z-index: 999;
    padding: 22px 30px 18px 30px; margin-bottom: 22px;
    background: linear-gradient(180deg, #0C0F18 0%, #070911 100%);
    border: 1px solid rgba(59,130,246,0.25);
    border-bottom: 2px solid rgba(59,130,246,0.55);
    border-radius: 16px;
    box-shadow: 0 6px 30px rgba(59,130,246,0.18), inset 0 -18px 30px -20px rgba(59,130,246,0.25);
}
.navbar-top-row {
    display: flex; align-items: center; justify-content: space-between;
    gap: 20px; flex-wrap: wrap;
}
.navbar-brand { display: flex; align-items: center; gap: 16px; }
.navbar-logo {
    width: 54px; height: 54px; border-radius: 14px; flex-shrink: 0;
    background: radial-gradient(circle, rgba(59,130,246,0.22), rgba(59,130,246,0.05));
    display: flex; align-items: center; justify-content: center;
    border: 1px solid rgba(59,130,246,0.4);
    box-shadow: 0 0 26px var(--blue-glow);
}
.navbar-logo svg { width: 30px; height: 30px; }
.navbar-title {
    font-family: 'Orbitron', 'Inter', sans-serif;
    font-size: 32px; font-weight: 800; line-height: 1;
    color: #7FD4FF; letter-spacing: 1px;
    text-shadow: 0 0 10px rgba(59,130,246,0.85), 0 0 34px rgba(59,130,246,0.45);
    margin: 0;
}
.navbar-tagline {
    font-size: 10.5px; font-weight: 700; letter-spacing: 2.6px;
    text-transform: uppercase; color: var(--text-dim); margin-top: 5px;
}
.navbar-context {
    text-align: right; font-size: 11px; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase; color: var(--text-dim);
}
.navbar-context b { color: var(--blue); font-weight: 800; }
.navbar-context .sep { color: var(--border); margin: 0 8px; }

.navbar-apps-row {
    display: flex; align-items: center; justify-content: flex-end;
    gap: 8px; flex-wrap: wrap; margin-top: 14px;
}
.navbar-app {
    display: flex; align-items: center; gap: 7px;
    padding: 7px 14px; border-radius: 9px;
    font-size: 12px; font-weight: 700; color: var(--text-dim);
    border: 1px solid transparent; white-space: nowrap;
    transition: all .15s ease;
}
.navbar-app.active {
    background: rgba(59,130,246,0.14); color: #7FD4FF;
    border: 1px solid rgba(59,130,246,0.4);
    box-shadow: 0 0 14px rgba(59,130,246,0.2);
}
.navbar-app.ghost {
    color: var(--text-dim); border: 1px dashed var(--border);
}
.navbar-app.ghost:hover { color: var(--text); border-color: var(--blue); }

/* ---------- Section headers ---------- */
.section-head { display:flex; align-items:center; gap:10px; margin: 22px 0 10px 0; }
.section-head .icon-chip {
    width: 30px; height: 30px; border-radius: 9px;
    background: var(--surface-2); border: 1px solid var(--border);
    display:flex; align-items:center; justify-content:center; color: var(--blue);
}
.section-head h3 { margin:0; font-size: 16.5px; font-weight: 700; color: var(--text); }
.section-sub { color: var(--text-dim); font-size: 12.8px; margin: -2px 0 14px 40px; }

/* ---------- Stepper ---------- */
.stepper { display:flex; align-items:center; width:100%; margin: 4px 0 26px 0; }
.step { display:flex; align-items:center; gap:8px; flex:1; }
.step .dot {
    width: 26px; height: 26px; border-radius: 50%;
    display:flex; align-items:center; justify-content:center;
    font-size: 11px; font-weight: 700; flex-shrink:0;
    border: 2px solid var(--border); color: var(--text-dim); background: var(--surface);
}
.step.done .dot { background: var(--emerald); border-color: var(--emerald); color: #06120D; }
.step.active .dot { background: var(--blue); border-color: var(--blue); color: #fff; box-shadow: 0 0 0 4px var(--blue-glow); }
.step .label { font-size: 12px; color: var(--text-dim); font-weight: 600; white-space:nowrap; }
.step.active .label, .step.done .label { color: var(--text); }
.step .line { flex:1; height: 2px; background: var(--border); margin: 0 6px; }
.step.done .line, .step.active ~ .step .line {background: var(--border);}

/* ---------- KPI cards ---------- */
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px 18px;
    transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
    height: 100%;
}
.kpi-card:hover { transform: translateY(-3px); border-color: rgba(59,130,246,0.4); box-shadow: 0 10px 26px rgba(0,0,0,0.35); }
.kpi-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
.kpi-icon { width:32px; height:32px; border-radius:9px; display:flex; align-items:center; justify-content:center; }
.kpi-label { color: var(--text-dim); font-size: 11.5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; }
.kpi-value { font-size: 23px; font-weight: 800; color: var(--text); font-family:'JetBrains Mono',monospace; }
.kpi-blue .kpi-icon { background: rgba(59,130,246,0.14); color: var(--blue); }
.kpi-emerald .kpi-icon { background: rgba(16,185,129,0.14); color: var(--emerald); }
.kpi-amber .kpi-icon { background: rgba(245,158,11,0.14); color: var(--amber); }
.kpi-red .kpi-icon { background: rgba(239,68,68,0.14); color: var(--red); }

/* ---------- Badges & chips ---------- */
.badge { display:inline-flex; align-items:center; gap:6px; padding: 4px 11px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.badge-found { background: rgba(16,185,129,0.14); color: var(--emerald); border: 1px solid rgba(16,185,129,0.3); }
.badge-partial { background: rgba(245,158,11,0.14); color: var(--amber); border: 1px solid rgba(245,158,11,0.3); }
.badge-few { background: rgba(249,115,22,0.14); color: #FB923C; border: 1px solid rgba(249,115,22,0.3); }
.badge-notfound { background: rgba(239,68,68,0.14); color: var(--red); border: 1px solid rgba(239,68,68,0.3); }

.chip { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; margin:3px 5px 3px 0; border-radius:8px; font-size:11.5px; font-weight:600; }
.chip-match { background: rgba(16,185,129,0.12); color: var(--emerald); border:1px solid rgba(16,185,129,0.25); }
.chip-mismatch { background: rgba(239,68,68,0.12); color: var(--red); border:1px solid rgba(239,68,68,0.25); }

/* ---------- Review card ---------- */
.review-card-head { display:flex; align-items:center; justify-content:space-between; width:100%; }
.review-desig { font-weight:700; color: var(--text); font-family:'JetBrains Mono',monospace; }
.review-score { color: var(--text-dim); font-size:12px; font-weight:600; margin-left:8px; }

/* ---------- Buttons ---------- */
.stButton>button {
    border-radius: 10px !important; font-weight: 700 !important;
    border: 1px solid var(--border) !important;
    transition: all .15s ease !important;
}
.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
    box-shadow: 0 4px 18px var(--blue-glow) !important;
    border: none !important;
}
.stButton>button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 8px 24px var(--blue-glow) !important; }

/* ---------- Uploader ---------- */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surface) !important;
    border: 1.5px dashed rgba(59,130,246,0.4) !important;
    border-radius: 16px !important;
}

/* ---------- Expander ---------- */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {
    background: var(--surface) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stExpander"] { border-radius: 12px !important; margin-bottom: 8px; }

/* ---------- Dataframe / editor container ---------- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background: #0D0F14 !important; border-right: 1px solid var(--border); }
.sidebar-logo { display:flex; align-items:center; gap:10px; padding: 6px 0 14px 0; }
.sidebar-version { color: var(--text-dim); font-size: 11px; }
.sidebar-block {
    background: var(--surface); border:1px solid var(--border); border-radius:12px;
    padding: 12px 14px; margin-bottom: 12px;
}
hr {border-color: var(--border) !important;}

/* Number/text inputs */
input, .stNumberInput input { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)


def section_head(icon_name, title, subtitle=None):
    render_html(f"""
    <div class="bomiq-section">
      <div class="section-head">
        <div class="icon-chip">{icon(icon_name)}</div>
        <h3>{title}</h3>
      </div>
      {f'<div class="section-sub">{subtitle}</div>' if subtitle else ''}
    </div>
    """)


def kpi_card(icon_name, label, value, accent="blue"):
    return f"""
    <div class="kpi-card kpi-{accent}">
        <div class="kpi-top">
            <div class="kpi-icon">{icon(icon_name)}</div>
        </div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """


def fmt_duration(seconds):
    seconds = max(0, seconds)
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {sec:.0f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m"


def status_badge_html(status):
    mapping = {
        "Found": ("badge-found", "🟢", "Found"),
        "Partially Matched": ("badge-partial", "🟡", "Partially Matched"),
        "Few Parameters Matched": ("badge-few", "🟠", "Few Parameters Matched"),
    }
    cls, dot, label = mapping.get(status, ("badge-notfound", "🔴", "Not Found"))
    return f'<span class="badge {cls}">{dot} {label}</span>'


# ==========================================================
# STEPPER  (visual progress tracker — display only)
# ==========================================================



# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    render_html(f"""
    <div class="sidebar-logo">
        {icon('logo')}
        <div>
            <div style="font-weight:800; font-size:18px; color:#E6E8EC; line-height:1;">BOMIQ</div>
            <div class="sidebar-version">v2.1.0 · Enterprise</div>
        </div>
    </div>
    """)

    render_html(
        '<div style="color:#8B90A0; font-size:12.5px; margin-bottom:14px;">'
        'Smart BOM Intelligence for Faster Electronics Sourcing</div>'
    )

    st.markdown("##### 🔌 Sourcing Config")

    distributor = st.selectbox(
        "Distributor",
        [
            "DigiKey"
        ],
        disabled=st.session_state.search_completed
    )

    currency = st.selectbox(
        "Currency",
        [
            "INR"
        ],
        disabled=st.session_state.search_completed
    )



    st.markdown("##### ⏱️ Benchmark Settings")

    manual_minutes_per_part = st.number_input(
        "Manual search time / component (min)",
        min_value=1.0,
        max_value=60.0,
        value=2.0,
        step=1.0,
        help="Estimated time an engineer spends manually looking up, "
             "cross-referencing, and pricing a single component. Used "
             "to calculate the speed comparison shown after a search.",
        disabled=st.session_state.search_completed
    )

    st.divider()

    api_placeholder = st.empty()

    with st.expander("⚙️ About BOMIQ"):
        st.markdown(
            "**BOMIQ** is an intelligent BOM sourcing and validation "
            "platform that automates component selection, validation, "
            "costing, and procurement."
        )
        st.caption("Version 1.0.0 · Build 2026.07")

def update_api_panel():

    stats = get_api_stats()

    with api_placeholder.container():

        st.markdown("### 🔌 DigiKey API")

        # -------------------------
        # Status
        # -------------------------

        if stats["connected"]:

            st.success("🟢 Connected")

        else:

            st.error("🔴 Disconnected")

        # -------------------------
        # Daily Requests
        # -------------------------

        if (
            stats["daily_remaining"] is not None
            and stats["daily_limit"] is not None
        ):

            remaining = int(stats["daily_remaining"])
            limit = int(stats["daily_limit"])

            st.write(
                f"**Daily Requests**  \n"
                f"{remaining} / {limit} Remaining"
            )

            st.progress(
                remaining / limit
            )

        else:

            st.write(
                "**Daily Requests**"
            )

            st.write("Unknown")

        # -------------------------
        # Session Calls
        # -------------------------

        st.write(
            f"**API Calls This Session**  \n"
            f"{stats['session_calls']}"
        )

update_api_panel()
 

# ==========================================================
# HEADER / NAVBAR
# ==========================================================
# This is the top-level app shell. Add new in-built apps here as
# additional `<div class="navbar-app">{icon} Label</div>` entries
# inside .navbar-apps-row (mark the currently open one with class
# "navbar-app active"). The right-aligned context line above it
# describes whichever app is currently open.

render_html(f"""
<div class="bomiq-navbar">
    <div class="navbar-top-row">
        <div class="navbar-brand">
            <div class="navbar-logo">{icon('logo')}</div>
            <div>
                <div class="navbar-title">BOMIQ</div>
                <div class="navbar-tagline">Smart BOM Intelligence Platform</div>
            </div>
        </div>
        <div class="navbar-context">
            <b>BOM Automation</b><span class="sep">·</span>Sourcing &amp; Validation<span class="sep">·</span>DigiKey Backend
        </div>
    </div>
    <div class="navbar-apps-row">
        <div class="navbar-app active">{icon('cpu')} BOM Automation</div>
        <div class="navbar-app ghost">+ Add App</div>
    </div>
</div>
""")

# ==========================================================
# UPLOAD
# ==========================================================

section_head("upload", "Upload BOM", "Upload an Altium BOM export (Comment, Designator, Quantity, LibRef).")

uploaded_file = st.file_uploader(
    "Upload Excel BOM",
    type=["xlsx"],
    label_visibility="collapsed"
)

if uploaded_file is not None:

    if (
        "last_uploaded_file" not in st.session_state
        or st.session_state.last_uploaded_file != uploaded_file.name
    ):

        raw_df = pd.read_excel(uploaded_file)

        mapped_df = standardize_bom(raw_df)

        engineering_df = generate_engineering_bom(mapped_df)

        st.session_state.engineering_bom = engineering_df

        st.session_state.search_completed = False
        st.session_state.search_results = None
        st.session_state.search_duration = None

        st.session_state.last_uploaded_file = uploaded_file.name


    st.success(f"✅ **{uploaded_file.name}** processed successfully — Engineering BOM generated.")

# ==========================================================
# ENGINEERING BOM
# ==========================================================

if st.session_state.engineering_bom is not None:

    section_head("cpu", "Engineering BOM", "Review and edit extracted parameters before searching DigiKey.")

    edited_df = st.data_editor(

        st.session_state.engineering_bom,

        hide_index=True,

        use_container_width=True,

        num_rows="dynamic",

        column_config={

            "Part Type": st.column_config.SelectboxColumn(
                "Part Type",
                options=[
                    "",
                    "Resistor",
                    "Ceramic Capacitor",
                    "Electrolytic Capacitor",
                    "Inductor",
                    "Diode",
                    "Zener",
                    "TVS",
                    "Bridge Rectifier",
                    "MOV",
                    "NTC",
                    "IC",
                    "Optocoupler"
                ]
            ),

            "Quantity": st.column_config.NumberColumn(
                "Quantity",
                min_value=1,
                step=1,
                default=1
            ),

            "Package": st.column_config.SelectboxColumn(
                "Package",
                options=[
                    "",
                    "0402",
                    "0603",
                    "0805",
                    "1206",
                    "1210",
                    "1812",
                    "2010",
                    "2512"
                ]
            ),

            "Tolerance": st.column_config.SelectboxColumn(
                "Tolerance",
                options=[
                    "",
                    "0.1%",
                    "0.5%",
                    "1%",
                    "2%",
                    "5%",
                    "10%",
                    "20%"
                ]
            ),

            "Power Rating": st.column_config.SelectboxColumn(
                "Power Rating",
                options=[
                    "",
                    "0.063W",
                    "0.1W",
                    "0.125W",
                    "0.25W",
                    "0.5W",
                    "1W",
                    "2W"
                ]
            ),

            "Voltage Rating": st.column_config.SelectboxColumn(
                "Voltage Rating",
                options=[
                    "",
                    "6.3V",
                    "10V",
                    "16V",
                    "25V",
                    "35V",
                    "50V",
                    "63V",
                    "100V",
                    "250V",
                    "400V",
                    "630V"
                ]
            ),

            "Dielectric": st.column_config.SelectboxColumn(
                "Dielectric",
                options=[
                    "",
                    "C0G",
                    "NP0",
                    "X5R",
                    "X7R",
                    "Y5V"
                ]
            )

        }

    )

    edited_df = edited_df.fillna("")
    edited_df.reset_index(drop=True, inplace=True)

    st.session_state.engineering_bom = edited_df

    section_head(
        "target",
        "Cost Analysis (Optional)",
        "Choose whether to compare against a target BOM cost or simply calculate the total BOM cost."
    )

    comparison_mode = st.radio(
        "Cost Analysis Mode",
        [
            "💰 Just calculate the BOM cost",
            "🎯 Compare with a target BOM cost"
        ],
        horizontal=True,
        label_visibility="collapsed",
        disabled=st.session_state.search_completed
    )
    # st.write("search_completed =", st.session_state.search_completed)
    if comparison_mode == "🎯 Compare with a target BOM cost":

        st.session_state.enable_cost_comparison = True

        st.number_input(
            "Enter Target BOM Cost (₹)",
            min_value=1.0,
            value=max(1.0, st.session_state.target_cost),
            step=1.0,
            format="%.2f",
            label_visibility="collapsed",
            disabled=st.session_state.search_completed
        )

    else:

        st.session_state.enable_cost_comparison = False
        st.session_state.target_cost = None

    st.write("")


    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        if st.button(
            "🔍  Search DigiKey",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.search_completed = True

            section_head("search", "Live Sourcing Activity", "Searching DigiKey and validating each component in real time.")

            search_container = st.container()
            with search_container:
                render_html(
                    '<div style="background:var(--surface);border:1px solid var(--border);'
                    'border-radius:14px;padding:16px 18px;">'
                )

                progress_bar = st.progress(0)
                status_text = st.empty()

                search_start_time = time.time()

                edited_df = st.session_state.engineering_bom.copy()

                # Remove completely empty rows
                edited_df = edited_df.dropna(how="all")

                # Remove rows without a designator
                edited_df = edited_df[
                    edited_df["Designator"].astype(str).str.strip() != ""
                ]

                edited_df.reset_index(drop=True, inplace=True)

                st.session_state.engineering_bom = edited_df

                from digikey_api import API_STATS

                API_STATS["status"] = "Connecting"
                API_STATS["connected"] = False

                st.session_state.search_results = search_bom(

                    st.session_state.engineering_bom,

                    target_cost=(
                        st.session_state.target_cost
                        if st.session_state.enable_cost_comparison
                        else None
                    ),

                    progress_bar=progress_bar,

                    status_text=status_text,

                    api_callback=update_api_panel

                )

                st.session_state.search_completed = True
                st.session_state.api_stats = get_api_stats().copy()

                st.session_state.search_duration = time.time() - search_start_time

                progress_bar.progress(1.0)
                status_text.success(
                    f"✅ Search Complete — all components processed in "
                    f"{fmt_duration(st.session_state.search_duration)}."
                )

                st.rerun()

                render_html('</div>')

# ==========================================================
# RESULTS
# ==========================================================

if st.session_state.search_results is not None:

    result = st.session_state.search_results

    summary_df = result["summary"]
    details_df = result["details"]
    dashboard = result["dashboard"]


    section_head(
    "chart",
    "Search Summary",
    "Cost performance and validation outcomes at a glance."
    )

    if st.session_state.enable_cost_comparison:

        cost1, cost2, cost3, cost4 = st.columns(4)

        with cost1:
            render_html(
                kpi_card(
                    "target",
                    "Target Cost",
                    f"₹{dashboard['Target Cost']:,.2f}",
                    "blue"
                )
            )

        with cost2:
            render_html(
                kpi_card(
                    "chart",
                    "Actual Cost",
                    f"₹{dashboard['Actual Cost']:,.2f}",
                    "emerald"
                )
            )

        with cost3:

            diff_accent = (
                "red"
                if dashboard["Difference"] > 0
                else "emerald"
            )

            render_html(
                kpi_card(
                    "chart",
                    "Difference",
                    f"₹{dashboard['Difference']:,.2f}",
                    diff_accent
                )
            )

        with cost4:
            render_html(
                kpi_card(
                    "chart",
                    "Difference %",
                    f"{dashboard['Difference %']:.2f}%",
                    diff_accent
                )
            )

    else:

        render_html(
            kpi_card(
                "money",
                "Final BOM Cost",
                f"₹{dashboard['Actual Cost']:,.2f}",
                "emerald"
            )
        )

    st.write("")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        render_html(
            kpi_card(
                "layers",
                "Total Parts",
                dashboard["Total Parts"],
                "blue"
            )
        )

    with c2:
        render_html(
            kpi_card(
                "check",
                "Found",
                dashboard["Found"],
                "emerald"
            )
        )

    with c3:
        render_html(
            kpi_card(
                "alert",
                "Partial",
                dashboard["Partially Matched"],
                "amber"
            )
        )

    with c4:
        render_html(
            kpi_card(
                "alert",
                "Few Matched",
                dashboard["Few Parameters Matched"],
                "amber"
            )
        )

    with c5:
        render_html(
            kpi_card(
                "x",
                "Not Found",
                dashboard["Not Found"],
                "red"
            )
        )

    with c6:
        render_html(
            kpi_card(
                "bot",
                "Automation",
                f"{dashboard['Automation']}%",
                "blue"
            )
        )


    st.write()
    # --------------------------------------------------
    # Speed Comparison — BOMIQ vs. manual sourcing
    # --------------------------------------------------

    st.markdown(
            "<div style='height:18px;'></div>",
            unsafe_allow_html=True
        )    
    if st.session_state.search_duration is not None:

        bomiq_seconds = st.session_state.search_duration
        total_parts = dashboard["Total Parts"]
        human_seconds = total_parts * manual_minutes_per_part * 60

        time_saved = max(0, human_seconds - bomiq_seconds)
        speedup = (human_seconds / bomiq_seconds) if bomiq_seconds > 0 else 0

        with st.expander(
            f"BOMIQ saved you approximately {fmt_duration(time_saved)} of engineering effort",
            expanded=False
        ):

            section_head(
                "bot",
                "Engineering Time Saved",
                "BOMIQ automatically searched, validated and sourced your BOM. Here's how much manual engineering effort was saved."
            )

            sp1, sp2, sp3 = st.columns(3)

            with sp1:
                render_html(
                    kpi_card(
                        "search",
                        "BOMIQ Search Time",
                        fmt_duration(bomiq_seconds),
                        "blue"
                    )
                )

            with sp2:
                render_html(
                    kpi_card(
                        "cpu",
                        "Manual Estimate",
                        fmt_duration(human_seconds),
                        "amber"
                    )
                )

            with sp3:
                render_html(
                    kpi_card(
                        "bot",
                        "Speed Gain",
                        f"{speedup:.0f}× Faster",
                        "emerald"
                    )
                )

            bomiq_pct = (
                max(2, min(100, (bomiq_seconds / human_seconds) * 100))
                if human_seconds > 0
                else 100
            )

            comparison_html = f"""
            <div style="background:var(--surface); border:1px solid var(--border); border-radius:14px;
                        padding:18px 20px; margin-top:12px;">

                <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                    <div style="width:74px; font-size:12px; font-weight:700; color:var(--blue);">
                        BOMIQ
                    </div>

                    <div style="flex:1; background:var(--surface-2); border-radius:8px; height:14px; overflow:hidden;">
                        <div style="width:{bomiq_pct:.2f}%; height:100%;
                                    background:linear-gradient(90deg,#3B82F6,#60A5FA);
                                    border-radius:8px;">
                        </div>
                    </div>

                    <div style="width:84px; text-align:right; font-size:12px;
                                color:var(--text-dim);
                                font-family:'JetBrains Mono', monospace;">
                        {fmt_duration(bomiq_seconds)}
                    </div>
                </div>

                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:74px; font-size:12px; font-weight:700; color:var(--amber);">
                        Manual
                    </div>

                    <div style="flex:1; background:var(--surface-2); border-radius:8px; height:14px; overflow:hidden;">
                        <div style="width:100%; height:100%;
                                    background:linear-gradient(90deg,#F59E0B,#FBBF24);
                                    border-radius:8px;">
                        </div>
                    </div>

                    <div style="width:84px; text-align:right; font-size:12px;
                                color:var(--text-dim);
                                font-family:'JetBrains Mono', monospace;">
                        {fmt_duration(human_seconds)}
                    </div>
                </div>

                <div style="color:var(--text-dim); font-size:11px; margin-top:12px;">
                    Manual estimate assumes approximately
                    <b>{manual_minutes_per_part:.0f} minute(s)</b> per component for
                    datasheet lookup, distributor search, cross-referencing and pricing.
                    You can adjust this benchmark from the sidebar.
                </div>

            </div>
            """

            render_html(comparison_html)
    # --------------------------------------------------
    # Status Icon  (unchanged logic — text kept identical
    # for downstream compatibility; visual badges rendered
    # separately via the Styler below)
    # --------------------------------------------------

    if "Status" in summary_df.columns:

        def status_icon(status):

            if status == "Found":
                return "🟢 Found"

            elif status == "Partially Matched":
                return "🟡 Partially Matched"

            elif status == "Few Parameters Matched":
                return "🟠 Few Parameters Matched"

            else:
                return "🔴 Not Found"

        summary_df["Status"] = summary_df["Status"].apply(
            status_icon
        )

    # --------------------------------------------------
    # Price Formatting
    # --------------------------------------------------

    USD_TO_INR = 95.38  # Make configurable later

    summary_df["Unit Price"] = pd.to_numeric(
        summary_df["Unit Price"],
        errors="coerce"
    )

    summary_df["Unit Price"] = summary_df["Unit Price"].apply(
        lambda x: f"₹{x * USD_TO_INR:,.2f}" if pd.notna(x) else ""
    )

    # --------------------------------------------------
    # Score Formatting
    # --------------------------------------------------

    # Create a display copy so the original dataframe remains untouched
    display_df = summary_df.copy()

    if "Validation Score" in display_df.columns:

        display_df["Validation Score"] = (
            pd.to_numeric(
                display_df["Validation Score"],
                errors="coerce"
            )
            .fillna(0)
            .astype(int)
            .astype(str)
            + "%"
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=450
    )

    # st.dataframe(

    #     summary_df,

    #     use_container_width=True,

    #     hide_index=True,

    #     height=450

    # )

    section_head("alert", "Review Required", "Components that need manual attention before final approval.")

    details_df = st.session_state.search_results["details"]

    reviewed_any = False

    for _, row in details_df.iterrows():

        if row["Validation Score"] == 100:
            continue

        reviewed_any = True

        if row["Status"] == "Partially Matched":
            icon_ = "🟡"

        elif row["Status"] == "Few Parameters Matched":
            icon_ = "🟠"

        else:
            icon_ = "🔴"

        with st.expander(
            f"{icon_}  {row['Designator']}  ·  {row['Part Type']}  —  {row['Status']}  ({row['Validation Score']}%)"
        ):

            render_html(status_badge_html(row["Status"]))
            st.write("")

            st.markdown("**Matched Parameters**")

            matched = row["Matched"]

            if matched:
                chips = "".join(
                    f'<span class="chip chip-match">✔ {item.strip()}</span>'
                    for item in matched.split(",")
                )
                render_html(chips)
            else:
                st.write("None")

            st.write("")
            st.markdown("**Mismatched Parameters**")

            mismatched = row["Mismatched"]

            if mismatched:
                chips = "".join(
                    f'<span class="chip chip-mismatch">✖ {item.strip()}</span>'
                    for item in mismatched.split(",")
                )
                render_html(chips)
            else:
                st.write("None")

    if not reviewed_any:
        st.info("All components matched with a perfect validation score — nothing to review.")

    # ==========================================================
    # DETAILED RESULTS
    # ==========================================================

    section_head("layers", "Detailed BOM", "Complete DigiKey search results including validation details.")

    with st.expander("🔽 View Detailed BOM", expanded=False):

        st.dataframe(
            details_df,
            use_container_width=True,
            hide_index=True,
            height=500
        )

    # ==========================================================
    # DOWNLOAD
    # ==========================================================

    section_head("download", "Export", "Download the final validated BOM in your preferred format.")

    csv_data = details_df.to_csv(index=False).encode("utf-8")

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        details_df.to_excel(writer, index=False, sheet_name="Final BOM")
    excel_data = excel_buffer.getvalue()

    exp1, exp2, exp3 = st.columns(3)

    with exp1:
        st.download_button(
            label="📄  CSV",
            data=csv_data,
            file_name="Final_BOM.csv",
            mime="text/csv",
            use_container_width=True
        )

    with exp2:
        st.download_button(
            label="📊  Excel",
            data=excel_data,
            file_name="Final_BOM.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with exp3:

        if REPORTLAB_AVAILABLE:

            pdf_data = generate_pdf_bytes(
                details_df,
                dashboard=dashboard,
                distributor=distributor,
                title="BOMIQ — Final Procurement BOM"
            )

            st.download_button(
                label="🧾  PDF",
                data=pdf_data,
                file_name="Final_BOM.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        else:

            st.button(
                "🧾 PDF (needs reportlab)",
                disabled=True,
                use_container_width=True
            )

            st.caption(
                "Run `pip install reportlab` to enable PDF export."
            )

    # ==========================================================
    # SEARCH STATISTICS
    # ==========================================================

    section_head("settings", "Search Statistics", "Session summary and configuration.")

    col1, col2 = st.columns(2)

    with col1:

        render_html(f"""
        <div class="sidebar-block">
            <div style="font-weight:700; color:#E6E8EC; margin-bottom:6px;">Sourcing Configuration</div>
            <div style="color:#8B90A0; font-size:13px;">Distributor · <b style="color:#E6E8EC;">{distributor}</b></div>
            <div style="color:#8B90A0; font-size:13px;">Currency · <b style="color:#E6E8EC;">{currency}</b></div>
        </div>
        """)

    with col2:

        average_score = round(
            details_df["Validation Score"].mean(),
            2
        )

        render_html(f"""
        <div class="sidebar-block">
            <div style="font-weight:700; color:#10B981; margin-bottom:6px;">Validation Summary</div>
            <div style="color:#8B90A0; font-size:13px;">Average Score · <b style="color:#E6E8EC;">{average_score}%</b></div>
            <div style="color:#8B90A0; font-size:13px;">Components Processed · <b style="color:#E6E8EC;">{len(details_df)}</b></div>
        </div>
        """)

# ==========================================================
# FOOTER
# ==========================================================

st.divider()

render_html(
    '<div style="text-align:center; color:#8B90A0; font-size:12px; padding: 6px 0 18px 0;">'
    '⚡ <b style="color:#E6E8EC;">BOMIQ</b> · Smart BOM Intelligence for Faster Electronics Sourcing · '
    'Powered by DigiKey API</div>'
)