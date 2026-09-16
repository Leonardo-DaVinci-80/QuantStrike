import streamlit as st # type: ignore
from styles import load_css, render_theme_toggle
render_theme_toggle()
load_css()
st.set_page_config(page_title="QuantStrike — Portfolio", layout="wide")

st.title("💼 Portfolio")
st.info(
    "🚧 Coming soon — track your holdings, ROI, allocation, and "
    "portfolio-level risk metrics like Sharpe ratio."
)