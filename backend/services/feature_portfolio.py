from datetime import datetime, timezone
from backend.database.feature_store import db_session

def add_transaction(portfolio_id,asset_id,asset_name,side,quantity,unit_price,fees=0,currency='USD',transacted_at=None,note=''):
    side=side.upper(); q=float(quantity); price=float(unit_price); fees=float(fees)
    if side not in {'BUY','SELL'} or q<=0 or price<0 or fees<0: raise ValueError('Invalid side, quantity, price, or fees')
    ts=transacted_at or datetime.now(timezone.utc).isoformat()
    with db_session() as c:
        if side=='SELL':
            rows=c.execute('SELECT side,quantity FROM portfolio_transactions WHERE portfolio_id=? AND asset_id=?',(portfolio_id,asset_id)).fetchall()
            held=sum(r['quantity'] if r['side']=='BUY' else -r['quantity'] for r in rows)
            if q>held+1e-9: raise ValueError(f'Cannot sell {q:g}; recorded holdings are {held:g}')
        c.execute('INSERT INTO portfolio_transactions(portfolio_id,asset_id,asset_name,side,quantity,unit_price,fees,currency,transacted_at,note) VALUES(?,?,?,?,?,?,?,?,?,?)',(portfolio_id,asset_id,asset_name,side,q,price,fees,currency,ts,note))

def get_transactions(portfolio_id):
    with db_session() as c: rows=c.execute('SELECT * FROM portfolio_transactions WHERE portfolio_id=? ORDER BY transacted_at,id',(portfolio_id,)).fetchall()
    return [dict(r) for r in rows]

def holdings(portfolio_id):
    positions={}
    for tx in get_transactions(portfolio_id):
        aid=tx['asset_id']; p=positions.setdefault(aid,{'asset_id':aid,'asset_name':tx['asset_name'],'quantity':0.0,'cost_basis':0.0,'realized_pnl':0.0,'currency':tx['currency']})
        q,price,fees=tx['quantity'],tx['unit_price'],tx['fees']
        if tx['side']=='BUY': p['quantity']+=q; p['cost_basis']+=q*price+fees
        else:
            if q>p['quantity']+1e-9: raise ValueError(f'Invalid sell transaction for {aid}')
            avg=p['cost_basis']/p['quantity'] if p['quantity'] else 0
            p['realized_pnl']+=q*price-fees-avg*q; p['cost_basis']-=avg*q; p['quantity']-=q
    return [p for p in positions.values() if p['quantity']>1e-9]

def delete_holding_transactions(portfolio_id, asset_id):
    """
    Permanently delete all transactions for one asset in a portfolio.
    This also removes the transaction history used to calculate P&L.
    """
    with db_session() as c:
        cur = c.execute(
            """
            DELETE FROM portfolio_transactions
            WHERE portfolio_id = ? AND asset_id = ?
            """,
            (portfolio_id, asset_id),
        )
        return cur.rowcount
