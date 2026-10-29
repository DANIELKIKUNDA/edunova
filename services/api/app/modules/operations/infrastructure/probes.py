from sqlalchemy import text

def database_probe(engine):
    def probe():
        with engine.connect() as conn: conn.execute(text("SELECT 1"))
    return probe

def redis_probe(client):
    def probe():
        if client is None: return
        if not client.ping(): raise RuntimeError("redis ping failed")
    return probe
