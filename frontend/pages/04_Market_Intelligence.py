import streamlit as st
import pandas as pd
from frontend.feature_helpers import choose_asset
from backend.services.feature_market import compare_marketplaces,save_observation
from datetime import datetime,timezone
from styles import load_css, render_theme_toggle, style_plotly

render_theme_toggle()
load_css()

st.set_page_config(page_title='Market Intelligence | QuantStrike',layout='wide')
st.title('🌐 Cross-Market Intelligence')
st.warning('This page stores normalized observations; it does not yet fetch live prices from Steam, Skinport, Buff163, YouPin, or CSFloat. Add verified source adapters before treating comparisons as actionable.')
repo,variant=choose_asset(key='marketintel')
if variant:
    with st.expander('Manually record a marketplace observation'):
        with st.form('market_obs'):
            marketplace=st.selectbox('Marketplace',['Steam','Skinport','Buff163','YouPin','CSFloat','Other']); currency=st.selectbox('Currency',['USD','EUR','GBP','CNY']); condition=st.text_input('Condition / variant',variant.get('condition','')); price=st.number_input('Observed price',min_value=.01,value=max(.01,float(variant.get('latest_price') or 1))); observed=st.text_input('Observed at (ISO 8601 UTC)',datetime.now(timezone.utc).isoformat()); volume=st.number_input('Observed volume (optional; 0 = unknown)',min_value=0.0,value=0.0); save=st.form_submit_button('Save observation')
        if save:
            try: save_observation(variant['skin_id'],variant['name'],marketplace,observed,price,currency,condition,volume if volume else None); st.success('Observation saved.')
            except Exception as e: st.error(str(e))
    currency_filter=st.selectbox('Comparison currency',['All','USD','EUR','GBP','CNY'])
    result=compare_marketplaces(variant['skin_id'],None if currency_filter=='All' else currency_filter)
    if result['observations']:
        if result['dispersion_pct'] is not None: st.metric('Observed cross-market price dispersion',f"{result['dispersion_pct']:.2f}%")
        st.dataframe(pd.DataFrame(result['observations']),use_container_width=True,hide_index=True)
        st.caption(result['warning'])
    else: st.info('No marketplace observations stored for this asset yet. Use the form to seed observations while API adapters are implemented.')
