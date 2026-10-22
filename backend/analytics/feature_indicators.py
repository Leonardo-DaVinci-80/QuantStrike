import numpy as np
import pandas as pd

def to_ohlc(history, interval='1D'):
    aliases={'1D':'1D','1W':'1W','1H':'1h','4H':'4h'}
    if interval not in aliases: raise ValueError(f'Choose one of {list(aliases)}')
    if history is None or history.empty: return pd.DataFrame(columns=['timestamp','open','high','low','close','volume'])
    df=history.copy(); df['timestamp']=pd.to_datetime(df.timestamp,utc=True,errors='coerce')
    df['price']=pd.to_numeric(df.price,errors='coerce')
    df=df.dropna(subset=['timestamp','price']).sort_values('timestamp').set_index('timestamp')
    bars=df.price.resample(aliases[interval]).ohlc()
    bars['volume']=df.volume.resample(aliases[interval]).sum(min_count=1) if 'volume' in df else np.nan
    return bars.dropna(subset=['open','high','low','close']).reset_index()

def add_indicators(df,ma_window=20,rsi_window=14,bb_window=20,bb_std=2.0):
    out=df.copy(); close=pd.to_numeric(out['close'],errors='coerce')
    out['ma']=close.rolling(ma_window,min_periods=ma_window).mean()
    delta=close.diff(); gain=delta.clip(lower=0).rolling(rsi_window,min_periods=rsi_window).mean(); loss=(-delta.clip(upper=0)).rolling(rsi_window,min_periods=rsi_window).mean()
    rs=gain/loss.replace(0,np.nan); out['rsi']=100-100/(1+rs)
    mid=close.rolling(bb_window,min_periods=bb_window).mean(); std=close.rolling(bb_window,min_periods=bb_window).std(ddof=0)
    out['bb_mid']=mid; out['bb_upper']=mid+bb_std*std; out['bb_lower']=mid-bb_std*std
    return out
