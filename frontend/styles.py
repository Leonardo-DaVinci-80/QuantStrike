import streamlit as st


# ============================================================
# QUANTSTRIKE THEME DEFINITIONS
# ============================================================

DARK_THEME = {
    "bg": "#0A0806",
    "card": "#14100C",
    "button": "#1C1611",
    "header": "#221A13",

    "border": "#362519",
    "border_button": "#5C3F2B",

    "text": "#FDF8EB",
    "text_muted": "#AFA79B",

    "accent": "#E28743",

    "positive": "#4ADE80",
    "negative": "#F87171",

    "grid": "#362519",
}


LIGHT_THEME = {
    "bg": "#F4F0E8",
    "card": "#FFFDF8",
    "button": "#F8F3EA",
    "header": "#EDE5D8",

    "border": "#D6C8B8",
    "border_button": "#B89572",

    "text": "#000000",
    "text_muted": "#6F655B",

    "accent": "#B85F20",

    "positive": "#168A4A",
    "negative": "#C83E3E",

    "grid": "#D6C8B8",
}


# ============================================================
# THEME STATE
# ============================================================

def get_theme():
    """
    Returns the currently selected QuantStrike theme.
    Defaults to dark mode.
    """

    if "quantstrike_theme" not in st.session_state:
        st.session_state.quantstrike_theme = "dark"

    return st.session_state.quantstrike_theme


def get_colors():
    """
    Returns the color dictionary for the active theme.
    """

    return (
        DARK_THEME
        if get_theme() == "dark"
        else LIGHT_THEME
    )


# ============================================================
# THEME TOGGLE
# ============================================================

def render_theme_toggle():
    """
    Renders the Dark / Light mode switch in the sidebar.
    """

    if "quantstrike_theme" not in st.session_state:
        st.session_state.quantstrike_theme = "dark"

    is_light = st.session_state.quantstrike_theme == "light"

    light_mode = st.sidebar.toggle(
        "Light mode",
        value=is_light,
        key="quantstrike_light_toggle",
    )

    new_theme = "light" if light_mode else "dark"

    if new_theme != st.session_state.quantstrike_theme:
        st.session_state.quantstrike_theme = new_theme
        st.rerun()


# ============================================================
# GLOBAL CSS
# ============================================================

def load_css():
    """
    Loads the complete QuantStrike UI theme.
    """

    colors = get_colors()

    st.markdown(
        f"""
        <style>

            /* Hide Streamlit's built-in theme/settings controls */
        [data-testid="stToolbar"] {{
            display: none !important;
        }}

        button[aria-label="Settings"] {{
            display: none !important;
        }}
        /* ====================================================
           QUANTSTRIKE — GLOBAL VARIABLES
           ==================================================== */

        :root {{
            --qs-bg: {colors["bg"]};
            --qs-card: {colors["card"]};
            --qs-button: {colors["button"]};
            --qs-header: {colors["header"]};

            --qs-border: {colors["border"]};
            --qs-border-button: {colors["border_button"]};

            --qs-text: {colors["text"]};
            --qs-text-muted: {colors["text_muted"]};

            --qs-accent: {colors["accent"]};

            --qs-positive: {colors["positive"]};
            --qs-negative: {colors["negative"]};

            --qs-grid: {colors["grid"]};

            --qs-font-mono:
                "JetBrains Mono",
                "Roboto Mono",
                "SFMono-Regular",
                Consolas,
                "Liberation Mono",
                monospace;
        }}


        /* ====================================================
           MAIN APPLICATION
           ==================================================== */

        .stApp {{
            background-color: var(--qs-bg) !important;
            color: var(--qs-text) !important;
        }}

        .main {{
            background-color: var(--qs-bg) !important;
        }}

        .main .block-container {{
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}


        /* ====================================================
           HEADER
           ==================================================== */

        header[data-testid="stHeader"] {{
            background-color: var(--qs-bg) !important;
        }}


        /* ====================================================
           SIDEBAR
           ==================================================== */

        section[data-testid="stSidebar"] {{
            background-color: var(--qs-card) !important;
            border-right: 1px solid var(--qs-border) !important;
        }}

        section[data-testid="stSidebar"] > div {{
            background-color: var(--qs-card) !important;
        }}

        section[data-testid="stSidebar"] .block-container {{
            background-color: var(--qs-card) !important;
        }}

        /* Sidebar text */

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{
            color: var(--qs-text) !important;
        }}

        /* Sidebar headings */

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: var(--qs-text) !important;
            font-family: var(--qs-font-mono) !important;
        }}

        /* Sidebar navigation links */

        section[data-testid="stSidebar"] a {{
            color: var(--qs-text-muted) !important;
            font-family: var(--qs-font-mono) !important;
            border-radius: 2px;
            transition:
                background-color 0.15s ease,
                color 0.15s ease;
        }}

        section[data-testid="stSidebar"] a:hover {{
            background-color: var(--qs-header) !important;
            color: var(--qs-accent) !important;
        }}

        /* Active sidebar navigation item */

        section[data-testid="stSidebar"] a[aria-current="page"] {{
            background-color: var(--qs-header) !important;
            color: var(--qs-accent) !important;
            border-left: 2px solid var(--qs-accent) !important;
        }}


        /* ====================================================
           GENERAL TEXT
           ==================================================== */
        .stMarkdown,
        [data-testid="stMarkdownContainer"] {{
            color: var(--qs-text) !important;
        }}

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] span {{
            color: var(--qs-text) !important;
        }}

        .stCaption {{
            color: var(--qs-text-muted) !important;
        }}
        /* ====================================================
           HEADINGS
           ==================================================== */

        h1,
        h2,
        h3,
        h4,
        h5,
        h6 {{
            color: var(--qs-text) !important;
        }}

        h1,
        h2,
        h3 {{
            font-family: var(--qs-font-mono) !important;
        }}

        h1 {{
            font-weight: 700 !important;
            letter-spacing: -0.03em;
        }}

        h2 {{
            font-weight: 600 !important;
        }}

        h3 {{
            font-weight: 600 !important;
        }}


        /* ====================================================
           CONTAINERS / CARDS
           ==================================================== */

        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: var(--qs-card) !important;
            border: 1px solid var(--qs-border) !important;
            border-radius: 2px !important;
        }}


        /* ====================================================
           METRICS
           ==================================================== */

        [data-testid="stMetric"] {{
            background-color: var(--qs-card) !important;
            border: 1px solid var(--qs-border) !important;
            border-radius: 2px !important;
            padding: 16px !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--qs-text-muted) !important;
            font-family: var(--qs-font-mono) !important;
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--qs-text) !important;
            font-family: var(--qs-font-mono) !important;
            font-size: 1.65rem !important;
            font-weight: 700 !important;
        }}

        [data-testid="stMetricDelta"] {{
            font-family: var(--qs-font-mono) !important;
        }}


        /* ====================================================
           BUTTONS
           ==================================================== */

        .stButton > button {{
            background-color: var(--qs-button) !important;
            color: var(--qs-accent) !important;

            border: 1px solid var(--qs-border-button) !important;
            border-radius: 2px !important;

            font-family: var(--qs-font-mono) !important;
            font-weight: 600 !important;

            transition:
                background-color 0.15s ease,
                color 0.15s ease,
                border-color 0.15s ease;
        }}

        .stButton > button:hover {{
            background-color: var(--qs-accent) !important;
            color: var(--qs-bg) !important;
            border-color: var(--qs-text) !important;
        }}

        .stButton > button:focus {{
            box-shadow: 0 0 0 1px var(--qs-accent) !important;
        }}


        /* ====================================================
           SELECTBOX
           ==================================================== */

        [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
            background-color: var(--qs-card) !important;
            color: var(--qs-text) !important;
            border-color: var(--qs-border) !important;
            border-radius: 2px !important;
        }}

        [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div {{
            border-color: var(--qs-accent) !important;
            box-shadow: 0 0 0 1px var(--qs-accent) !important;
        }}

        [data-testid="stSelectbox"] input {{
            color: var(--qs-text) !important;
            font-family: var(--qs-font-mono) !important;
        }}


        /* ====================================================
           MULTISELECT
           ==================================================== */

        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
            background-color: var(--qs-card) !important;
            border-color: var(--qs-border) !important;
            border-radius: 2px !important;
        }}

        [data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div {{
            border-color: var(--qs-accent) !important;
            box-shadow: 0 0 0 1px var(--qs-accent) !important;
        }}

        [data-baseweb="tag"] {{
            background-color: var(--qs-header) !important;
            color: var(--qs-accent) !important;
            border: 1px solid var(--qs-border) !important;
            border-radius: 2px !important;
            font-family: var(--qs-font-mono) !important;
        }}


        /* ====================================================
           DROPDOWNS
           ==================================================== */

        [data-baseweb="popover"] {{
            background-color: var(--qs-card) !important;
            border: 1px solid var(--qs-border) !important;
        }}

        [data-baseweb="menu"] {{
            background-color: var(--qs-card) !important;
        }}

        [role="option"] {{
            background-color: var(--qs-card) !important;
            color: var(--qs-text) !important;
            font-family: var(--qs-font-mono) !important;
        }}

        [role="option"]:hover {{
            background-color: var(--qs-header) !important;
            color: var(--qs-accent) !important;
        }}


        /* ====================================================
           INPUTS
           ==================================================== */

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {{
            background-color: var(--qs-card) !important;
            color: var(--qs-text) !important;

            border: 1px solid var(--qs-border) !important;
            border-radius: 2px !important;

            font-family: var(--qs-font-mono) !important;
        }}

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus {{
            border-color: var(--qs-accent) !important;
            box-shadow: 0 0 0 1px var(--qs-accent) !important;
        }}


        /* ====================================================
           DATAFRAMES
           ==================================================== */

        [data-testid="stDataFrame"] {{
            border: 1px solid var(--qs-border) !important;
            border-radius: 2px !important;
            overflow: hidden;
        }}

        [data-testid="stDataFrame"] * {{
            font-family: var(--qs-font-mono) !important;
        }}


        /* ====================================================
           EXPANDERS
           ==================================================== */

        [data-testid="stExpander"] {{
            background-color: var(--qs-card) !important;
            border: 1px solid var(--qs-border) !important;
            border-radius: 2px !important;
        }}

        [data-testid="stExpander"] summary {{
            color: var(--qs-accent) !important;
            font-family: var(--qs-font-mono) !important;
            font-weight: 600 !important;
        }}


        /* ====================================================
           DIVIDERS
           ==================================================== */

        hr {{
            border-color: var(--qs-border) !important;
        }}


        /* ====================================================
           LINKS
           ==================================================== */

        a {{
            color: var(--qs-accent) !important;
        }}

        a:hover {{
            color: var(--qs-text) !important;
        }}


        /* ====================================================
           ALERTS
           ==================================================== */

        [data-testid="stAlert"] {{
            background-color: var(--qs-card) !important;
            border-radius: 2px !important;
            font-family: var(--qs-font-mono) !important;
        }}


        /* ====================================================
           SCROLLBAR
           ==================================================== */

        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: var(--qs-bg);
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--qs-border);
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--qs-accent);
        }}


        /* ====================================================
           TERMINAL UTILITY CLASSES
           ==================================================== */

        .terminal-label {{
            color: var(--qs-text-muted) !important;
            font-family: var(--qs-font-mono) !important;
            font-size: 0.7rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }}

        .terminal-value {{
            color: var(--qs-text) !important;
            font-family: var(--qs-font-mono) !important;
            font-weight: 700;
        }}

        .accent {{
            color: var(--qs-accent) !important;
        }}

        .positive {{
            color: var(--qs-positive) !important;
        }}

        .negative {{
            color: var(--qs-negative) !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PLOTLY THEME
# ============================================================

def style_plotly(fig):
    """
    Applies the QuantStrike theme to a Plotly figure.
    """

    colors = get_colors()

    fig.update_layout(
        paper_bgcolor=colors["bg"],
        plot_bgcolor=colors["card"],

        font=dict(
            family="JetBrains Mono, Roboto Mono, monospace",
            color=colors["text"],
        ),

        margin=dict(
            l=20,
            r=20,
            t=55,
            b=20,
        ),

        legend=dict(
            font=dict(
                family="JetBrains Mono, Roboto Mono, monospace",
                color=colors["text"],
            ),
            bgcolor="rgba(0,0,0,0)",
        ),

        hoverlabel=dict(
            bgcolor=colors["card"],
            bordercolor=colors["border"],
            font=dict(
                family="JetBrains Mono, Roboto Mono, monospace",
                color=colors["text"],
            ),
        ),
    )

    fig.update_xaxes(
        color=colors["text_muted"],
        gridcolor=colors["grid"],
        linecolor=colors["border"],
        zerolinecolor=colors["grid"],
        tickfont=dict(
            family="JetBrains Mono, Roboto Mono, monospace",
            color=colors["text_muted"],
        ),
    )

    fig.update_yaxes(
        color=colors["text_muted"],
        gridcolor=colors["grid"],
        linecolor=colors["border"],
        zerolinecolor=colors["grid"],
        tickfont=dict(
            family="JetBrains Mono, Roboto Mono, monospace",
            color=colors["text_muted"],
        ),
    )

    return fig