import streamlit as st
import pandas as pd


# ─── Global styling ────────────────────────────────────────────────────────
def inject_css():
    """Inject the clean & professional theme. Call once at app start."""
    st.markdown(
        """
        <style>
        /* Base layout */
        .stApp { background-color: #f5f7fa; }
        .block-container { padding-top: 2rem; max-width: 1300px; }
        [data-testid="stHeader"] { background: transparent; }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }

        /* App header banner */
        .app-header {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 5px solid #2563eb;
            border-radius: 14px;
            padding: 1.25rem 1.75rem;
            margin-bottom: 1.75rem;
            box-shadow: 0 1px 3px rgba(15,23,42,0.06);
        }
        .app-title {
            font-size: 1.9rem;
            font-weight: 700;
            color: #0f172a;
            margin: 0;
            line-height: 1.15;
        }
        .app-subtitle {
            color: #64748b;
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }

        /* Stat cards */
        .stat-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1.25rem 1.4rem;
            box-shadow: 0 1px 3px rgba(15,23,42,0.06);
            transition: transform .15s ease, box-shadow .15s ease;
            height: 100%;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 24px rgba(15,23,42,0.10);
        }
        .stat-icon {
            font-size: 1.6rem;
            line-height: 1;
            margin-bottom: 0.5rem;
        }
        .stat-value {
            font-size: 2.1rem;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.1;
        }
        .stat-label {
            color: #64748b;
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.2rem;
        }

        /* Severity badges */
        .badge {
            display: inline-block;
            padding: 0.18rem 0.7rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            line-height: 1.4;
        }
        .badge-critical { background: #fee2e2; color: #b91c1c; }
        .badge-high     { background: #ffedd5; color: #c2410c; }
        .badge-medium   { background: #fef9c3; color: #a16207; }
        .badge-low      { background: #dcfce7; color: #15803d; }
        .badge-warning  { background: #fef9c3; color: #a16207; }
        .badge-info     { background: #dbeafe; color: #1d4ed8; }
        .badge-neutral  { background: #e2e8f0; color: #475569; }

        /* Section headings */
        h2, h3 { color: #0f172a; }

        /* Buttons */
        .stButton > button {
            border-radius: 9px;
            border: 1px solid #2563eb;
            background: #2563eb;
            color: #ffffff;
            font-weight: 600;
            padding: 0.45rem 1.1rem;
            transition: background .15s ease;
        }
        .stButton > button:hover {
            background: #1d4ed8;
            border-color: #1d4ed8;
            color: #ffffff;
        }

        /* Dataframe container polish */
        [data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 0.4rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = "🚨"):
    """Styled app/page header banner."""
    sub = f'<div class="app-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="app-header"><div class="app-title">{icon} {title}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


# ─── Cards & badges ──────────────────────────────────────────────────────────
def stat_card(label, value, icon="📊"):
    """Render a single metric card (call inside a column)."""
    st.markdown(
        f'<div class="stat-card">'
        f'<div class="stat-icon">{icon}</div>'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


_BADGE_CLASS = {
    "Critical": "badge-critical",
    "High": "badge-high",
    "Medium": "badge-medium",
    "Low": "badge-low",
    "Warning": "badge-warning",
    "Info": "badge-info",
}


def severity_badge(severity: str) -> str:
    """Return an HTML pill badge for a severity value (use with unsafe_allow_html)."""
    cls = _BADGE_CLASS.get(severity, "badge-neutral")
    return f'<span class="badge {cls}">{severity}</span>'


def data_table(df: pd.DataFrame, title: str = None):
    if title:
        st.subheader(title)
    if df.empty:
        st.info("No data available.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)


def severity_color(severity):
    colors = {
        "Info": "🔵",
        "Warning": "🟡",
        "Critical": "🔴",
    }
    return colors.get(severity, "⚪")


def format_date(date_str):
    if not date_str:
        return "—"
    return str(date_str)[:10]


def severity_to_color(severity: str) -> list[int]:
    """Map disaster severity to RGBA color tuple."""
    colors = {
        "Critical": [220, 38, 38, 200],    # red
        "High": [234, 88, 12, 200],        # orange
        "Medium": [202, 138, 4, 200],      # yellow
        "Low": [22, 163, 74, 200],         # green
    }
    return colors.get(severity, [107, 114, 128, 200])  # gray fallback
