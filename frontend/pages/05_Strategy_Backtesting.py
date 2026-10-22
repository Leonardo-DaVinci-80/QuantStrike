import streamlit as st
import plotly.graph_objects as go
from frontend.feature_helpers import choose_asset
from backend.repositories.feature_history import FeatureHistoryRepository
from backend.analytics.feature_indicators import to_ohlc
from backend.analytics.feature_backtesting import backtest_sma
from styles import load_css, render_theme_toggle, style_plotly

render_theme_toggle()
load_css()

st.set_page_config(page_title='Strategy Backtesting | QuantStrike',layout='wide')
st.title('🧪 Strategy Backtesting')
st.caption('Baseline SMA crossover. Fees are simplified, slippage and marketplace-specific execution constraints are not modeled.')
repo,variant=choose_asset(key='backtest')
col1,col2,col3=st.columns(3); fast=col1.slider('Fast SMA',2,30,7); slow=col2.slider('Slow SMA',10,100,30); fee=col3.number_input('Fee per position change (fraction)',min_value=0.0,max_value=.2,value=.02,step=.005,format='%.3f')
if fast>=slow: st.error('Fast SMA must be smaller than slow SMA.')
if variant and st.button('Run backtest',type='primary'):
    try:
        history=FeatureHistoryRepository().get_history(variant['skin_id'],limit=20000); bars=to_ohlc(history,'1D')
        result=backtest_sma(bars,fast,slow,fee); a,b,c=st.columns(3); a.metric('Strategy return',f"{result['total_return_pct']:+.2f}%"); b.metric('Max drawdown',f"{result['max_drawdown_pct']:.2f}%"); c.metric('Annualized Sharpe (rough)',f"{result['sharpe']:.2f}" if result['sharpe'] is not None else 'N/A')
        df=result['history']; fig=go.Figure(); fig.add_trace(go.Scatter(x=df.timestamp,y=df.equity,name='Strategy equity')); fig.add_trace(go.Scatter(x=df.timestamp,y=df.buy_hold_equity,name='Buy & hold')); fig.update_layout(height=480,yaxis_title='Growth of 1.0'); st.plotly_chart(fig,use_container_width=True); st.dataframe(df.tail(100),use_container_width=True)
        st.caption(f"Assumptions: {result['assumptions']}")
    except Exception as e: st.error(f'Backtest could not run: {e}')
