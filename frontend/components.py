import streamlit as st # type:ignore
def section(title, icon=""):
    st.markdown(
        f"""
        <h2 style="margin-bottom:0.5rem;">
        {icon} {title}
        </h2>
        """,
        unsafe_allow_html=True
    )

def subsection(title):
    st.markdown(
        f"""
        <h3 style="margin-bottom:0.5rem;">
        {title}
        </h3>
        """,
        unsafe_allow_html=True
    )

def divider():
    st.divider()

def info_box(text):
    st.info(text)

def warning_box(text):
    st.warning(text)

def success_box(text):
    st.success(text)

def metric_card(label, value, delta=None):
    st.metric(
        label=label,
        value=value,
        delta=delta
    )

def metric_grid(metrics, columns=4):
    cols = st.columns(columns)
    for col, metric in zip(cols, metrics):
        with col:
            st.metric(
                metric["label"],
                metric["value"],
                metric.get("delta")
            )

def coming_soon(title, description):
    st.header(title)
    st.info(f"""🚧 **Coming Soon**{description}""")