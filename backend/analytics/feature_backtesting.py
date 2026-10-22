import numpy as np
import pandas as pd

def backtest_sma(bars,fast=7,slow=30,fee_rate=0.02):
    if fast<1 or slow<=fast: raise ValueError('Require 1 <= fast < slow')
    if not 0<=fee_rate<1: raise ValueError('fee_rate must be in [0,1)')
    df=bars.copy().sort_values('timestamp').reset_index(drop=True)
    if len(df)<slow+2: raise ValueError(f'Need at least {slow+2} bars')
    df['fast_ma']=df.close.rolling(fast).mean(); df['slow_ma']=df.close.rolling(slow).mean()
    df['position']=(df.fast_ma>df.slow_ma).astype(float).shift(1).fillna(0.0)
    df['asset_return']=df.close.pct_change().shift(-1)
    df['turnover']=df.position.diff().abs().fillna(df.position.abs())
    df['strategy_return']=df.position*df.asset_return-df.turnover*fee_rate
    df=df.dropna(subset=['asset_return']).copy()
    if df.empty: raise ValueError('No valid return observations after signal alignment')
    df['equity']=(1+df.strategy_return.fillna(0)).cumprod(); df['buy_hold_equity']=(1+df.asset_return.fillna(0)).cumprod()
    df['drawdown']=df.equity/df.equity.cummax()-1
    ret=df.strategy_return.dropna(); std=ret.std(ddof=1)
    sharpe=float(ret.mean()/std*np.sqrt(252)) if len(ret)>1 and std>0 else None
    return {'history':df,'total_return_pct':float((df.equity.iloc[-1]-1)*100),'max_drawdown_pct':float(df.drawdown.min()*100),'sharpe':sharpe,
      'assumptions':{'fee_rate_per_exposure_change':fee_rate,'execution':'signal lagged by one bar; close-to-close returns','slippage':'not modeled','not_a_trading_recommendation':True}}
