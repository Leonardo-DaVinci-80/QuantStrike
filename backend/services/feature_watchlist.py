from datetime import datetime, timezone, timedelta
from backend.database.feature_store import db_session

def add_item(asset_id,asset_name,user_id='local'):
    with db_session() as c: c.execute('INSERT OR IGNORE INTO watchlist(user_id,asset_id,asset_name) VALUES(?,?,?)',(user_id,asset_id,asset_name))
def remove_item(asset_id,user_id='local'):
    with db_session() as c: c.execute('DELETE FROM watchlist WHERE user_id=? AND asset_id=?',(user_id,asset_id))
def list_items(user_id='local'):
    with db_session() as c: return [dict(r) for r in c.execute('SELECT * FROM watchlist WHERE user_id=? ORDER BY created_at DESC',(user_id,)).fetchall()]
def create_alert(asset_id,metric,operator,threshold,cooldown_minutes=60,user_id='local'):
    if metric not in {'price','return_pct'} or operator not in {'>','>=','<','<='}: raise ValueError('Unsupported metric or operator')
    with db_session() as c:
        cur=c.execute('INSERT INTO alert_rules(user_id,asset_id,metric,operator,threshold,cooldown_minutes) VALUES(?,?,?,?,?,?)',(user_id,asset_id,metric,operator,float(threshold),max(0,int(cooldown_minutes))))
        return cur.lastrowid
def alert_rules(user_id='local'):
    with db_session() as c: return [dict(r) for r in c.execute('SELECT * FROM alert_rules WHERE user_id=? ORDER BY id DESC',(user_id,)).fetchall()]
def evaluate_alerts(values,now=None,user_id='local'):
    now=now or datetime.now(timezone.utc); fired=[]
    with db_session() as c:
        rules=c.execute('SELECT * FROM alert_rules WHERE enabled=1 AND user_id=?',(user_id,)).fetchall()
        for r in rules:
            value=values.get(r['asset_id'],{}).get(r['metric'])
            if value is None: continue
            match={'>':value>r['threshold'],'>=':value>=r['threshold'],'<':value<r['threshold'],'<=':value<=r['threshold']}[r['operator']]
            if not match: continue
            if r['last_triggered_at']:
                last=datetime.fromisoformat(r['last_triggered_at'].replace('Z','+00:00'))
                if now-last<timedelta(minutes=r['cooldown_minutes']): continue
            msg=f"{r['asset_id']}: {r['metric']}={value:g} {r['operator']} {r['threshold']:g}"
            c.execute('INSERT INTO alert_events(rule_id,observed_value,message,triggered_at) VALUES(?,?,?,?)',(r['id'],float(value),msg,now.isoformat()))
            c.execute('UPDATE alert_rules SET last_triggered_at=? WHERE id=?',(now.isoformat(),r['id'])); fired.append(msg)
    return fired
def alert_history(limit=100,user_id='local'):
    with db_session() as c: return [dict(r) for r in c.execute('SELECT e.* FROM alert_events e JOIN alert_rules r ON r.id=e.rule_id WHERE r.user_id=? ORDER BY e.triggered_at DESC LIMIT ?',(user_id,max(1,min(int(limit),1000)))).fetchall()]


def delete_alert_rule(rule_id, user_id="local"):
    """
    Delete an alert rule and its associated alert events.
    Other rules and their history remain unchanged.
    """
    with db_session() as c:
        existing = c.execute(
            """
            SELECT id
            FROM alert_rules
            WHERE id = ? AND user_id = ?
            """,
            (rule_id, user_id),
        ).fetchone()

        if existing is None:
            return False

        c.execute(
            "DELETE FROM alert_events WHERE rule_id = ?",
            (rule_id,),
        )

        c.execute(
            """
            DELETE FROM alert_rules
            WHERE id = ? AND user_id = ?
            """,
            (rule_id, user_id),
        )

    return True
