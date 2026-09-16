import streamlit as st # type: ignore
from styles import load_css, render_theme_toggle
render_theme_toggle()
load_css()

st.set_page_config(page_title="QuantStrike — Skin", layout="wide")

st.title("🔫 Skin Detail")
st.info(
    "🚧 Coming soon — dedicated deep-dive page per skin. "
    "For now, use the search on the Home page."
)