from backend.database.feature_store import db_session

def save_observation(asset_id,asset_name,marketplace,observed_at,price,currency,condition_name='',volume=None,source_ref=''):
    if float(price)<=0: raise ValueError('price must be positive')
    with db_session() as c:
        c.execute('INSERT INTO market_observations(asset_id,asset_name,marketplace,observed_at,price,currency,condition_name,volume,source_ref) VALUES(?,?,?,?,?,?,?,?,?)',(asset_id,asset_name,marketplace,observed_at,float(price),currency,condition_name,volume,source_ref))
def compare_marketplaces(asset_id,currency=None):
    with db_session() as c: rows=[dict(r) for r in c.execute('SELECT * FROM market_observations WHERE asset_id=? ORDER BY observed_at DESC',(asset_id,)).fetchall()]
    if currency: rows=[r for r in rows if r['currency'].upper()==currency.upper()]
    latest={}
    for r in rows: latest.setdefault((r['marketplace'],r['currency'],r['condition_name']),r)
    obs=list(latest.values()); prices=[r['price'] for r in obs]
    spread=(max(prices)-min(prices))/min(prices)*100 if prices and min(prices)>0 else None
    return {'observations':obs,'dispersion_pct':spread,'warning':'Compare item condition, currency, fees, liquidity and observation freshness before interpreting spreads.'}
