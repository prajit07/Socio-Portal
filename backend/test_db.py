import sys
sys.path.insert(0, '.')
from app.core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("DB Connection OK:", result.scalar())
except Exception as e:
    print("DB Connection FAILED:", e)