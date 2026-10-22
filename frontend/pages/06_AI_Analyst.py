import streamlit as st
from frontend.feature_helpers import choose_asset
from backend.repositories.feature_history import FeatureHistoryRepository
from backend.analytics.feature_indicators import to_ohlc,add_indicators
from backend.ai.market_ai import MarketAI
from styles import load_css, render_theme_toggle, style_plotly

render_theme_toggle()
load_css()

st.set_page_config(page_title='AI Analyst | QuantStrike',layout='wide')
st.title('🧠 QuantStrike AI Analyst')
st.caption('Uses the existing Gemini integration and sends a compact summary of the selected asset—not the raw full dataset.')
repo,variant=choose_asset(key='ai')
question=st.text_area('Question',placeholder='Summarize the recent trend and explain the main risks.')
if variant and st.button('Analyze',type='primary'):
    try:
        history=FeatureHistoryRepository().get_history(variant['skin_id'],limit=5000); bars=add_indicators(to_ohlc(history,'1D'))
        if bars.empty: st.warning('No historical observations available for this asset.')
        else:
            recent=bars.tail(60).copy(); facts={'asset':variant['name'],'observations_loaded':len(history),'daily_bars':len(bars),'first_bar':str(bars.timestamp.iloc[0]),'last_bar':str(bars.timestamp.iloc[-1]),'latest_close':float(bars.close.iloc[-1]),'return_over_loaded_period_pct':float((bars.close.iloc[-1]/bars.close.iloc[0]-1)*100) if bars.close.iloc[0]>0 else None,'latest_rsi_14':float(bars.rsi.dropna().iloc[-1]) if bars.rsi.notna().any() else None,'recent_daily_bars':recent[['timestamp','open','high','low','close','volume']].to_dict('records')}
            if not question.strip(): st.error('Enter a question first.')
            else: st.markdown(MarketAI().ask(question,str(facts)))
    except Exception as e: st.error(f'AI analysis failed: {e}. Check GEMINI_API_KEY and the installed google-genai version.')
