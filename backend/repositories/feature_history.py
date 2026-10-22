from pathlib import Path
import re
from datetime import datetime, timezone
import duckdb
import pandas as pd
from backend.config import HISTORY_PATH, HISTORY_TIMESTAMP, HISTORY_ASSET, HISTORY_PRICE, HISTORY_VOLUME, HISTORY_TIMESTAMP_FORMAT

def _ident(value):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value or ''):
        raise ValueError(f'Invalid configured column name: {value!r}')
    return '"'+value+'"'

class FeatureHistoryRepository:
    """Bounded DuckDB access for the existing skin_id/timestamp/price/volume Parquet."""
    def __init__(self, path=HISTORY_PATH): self.path=Path(path)

    def get_history(self, asset_id, limit=10000, start=None, end=None):
        if not self.path.exists(): raise FileNotFoundError(f'Historical Parquet not found: {self.path}')
        limit=max(1,min(int(limit),20000))
        ts, aid, price, vol=map(_ident,[HISTORY_TIMESTAMP,HISTORY_ASSET,HISTORY_PRICE,HISTORY_VOLUME])
        if HISTORY_TIMESTAMP_FORMAT == 'unix_seconds':
            ts_expr=f'TO_TIMESTAMP(TRY_CAST({ts} AS DOUBLE))'
            def bound(x):
                if x is None: return None
                stamp=pd.Timestamp(x)
                if stamp.tzinfo is None: stamp=stamp.tz_localize('UTC')
                return stamp.timestamp()
            comparison=ts
        elif HISTORY_TIMESTAMP_FORMAT == 'timestamp':
            ts_expr=f'TRY_CAST({ts} AS TIMESTAMP)'
            bound=lambda x: str(x) if x is not None else None
            comparison=ts
        else: raise ValueError('HISTORY_TIMESTAMP_FORMAT must be unix_seconds or timestamp')
        sql=f'SELECT {ts_expr} AS timestamp, TRY_CAST({price} AS DOUBLE) AS price, TRY_CAST({vol} AS DOUBLE) AS volume FROM read_parquet(?) WHERE CAST({aid} AS VARCHAR)=?'
        params=[str(self.path),str(asset_id)]
        if start is not None:
            sql+=f' AND {comparison} >= ?'; params.append(bound(start))
        if end is not None:
            sql+=f' AND {comparison} <= ?'; params.append(bound(end))
        sql+=f' ORDER BY {ts} DESC LIMIT ?'; params.append(limit)
        con=duckdb.connect()
        try: df=con.execute(sql,params).df()
        finally: con.close()
        if not df.empty:
            df['timestamp']=pd.to_datetime(df.timestamp,utc=True,errors='coerce')
            df['price']=pd.to_numeric(df.price,errors='coerce')
            df['volume']=pd.to_numeric(df.volume,errors='coerce').fillna(0)
            df=df.dropna(subset=['timestamp','price']).query('price > 0').sort_values('timestamp').reset_index(drop=True)
        return df
