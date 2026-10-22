import streamlit as st
import plotly.graph_objects as go
from frontend.feature_helpers import choose_asset
from backend.repositories.feature_history import FeatureHistoryRepository
from backend.analytics.feature_indicators import to_ohlc,add_indicators
from styles import load_css, render_theme_toggle, style_plotly

render_theme_toggle()
load_css()

st.set_page_config(page_title='Advanced Charting | QuantStrike',layout='wide')
st.title('📈 Advanced Charting')
st.caption('DuckDB queries fetch a bounded slice for the selected asset; the complete historical dataset is not loaded into pandas.')
repo,variant=choose_asset(key='chart')
col1,col2,col3=st.columns(3)
interval=col1.selectbox('Bar interval',['1D','1W','1H','4H'],index=0)
limit=col2.slider('Maximum source observations',100,20000,5000,100)
chart_kind=col3.selectbox('Chart type',['Candlestick','Line'])
show_ma=st.checkbox('Show 20-bar moving average',True)
show_bands=st.checkbox('Show Bollinger Bands',False)
if interval in {'1H','4H'}: st.warning('Intraday bars are only meaningful if the source observations are intraday. Daily data cannot reconstruct hourly price movement.')
if variant and st.button('Load chart',type='primary'):
    try:
        history=FeatureHistoryRepository().get_history(variant['skin_id'],limit=limit)
        bars=add_indicators(to_ohlc(history,interval))
        if bars.empty: st.warning('No usable history found for this variant.')
        else:
            fig=go.Figure()
            if chart_kind=='Line': fig.add_trace(go.Scatter(x=bars.timestamp,y=bars.close,name='Close',mode='lines'))
            else: fig.add_trace(go.Candlestick(x=bars.timestamp,open=bars.open,high=bars.high,low=bars.low,close=bars.close,name='Price'))
            if show_ma: fig.add_trace(go.Scatter(x=bars.timestamp,y=bars.ma,name='MA(20)',line={'dash':'dash'}))
            if show_bands:
                fig.add_trace(go.Scatter(x=bars.timestamp,y=bars.bb_upper,name='BB upper',line={'width':1},opacity=.6))
                fig.add_trace(go.Scatter(x=bars.timestamp,y=bars.bb_lower,name='BB lower',line={'width':1},opacity=.6,fill='tonexty'))
            fig.update_layout(height=560,xaxis_rangeslider_visible=False,legend_orientation='h')
            st.plotly_chart(fig,use_container_width=True)
            a,b,c=st.columns(3)
            if bars.close.iloc[0]>0: a.metric('Period return',f"{(bars.close.iloc[-1]/bars.close.iloc[0]-1)*100:+.2f}%")
            b.metric('Latest close',f"{bars.close.iloc[-1]:,.2f}")
            c.metric('Bars',f'{len(bars):,}')
            with st.expander('Indicator data'): st.dataframe(bars.tail(100),use_container_width=True)
    except Exception as e: st.error(f'Unable to load chart: {e}')
