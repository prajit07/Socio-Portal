"""Dev-only DB reset: drops all tables + enum types, then re-creates via Alembic.

Run:  python reset_db.py
"""
import os
import sys

from sqlalchemy import create_engine, text, inspect

sys.path.append(os.path.dirname(__file__))

from app.core.config import settings

URL = settings.DATABASE_URL
if URL.startswith("postgresql://"):
    URL = "postgresql+psycopg://" + URL[len("postgresql://"):]
if "sslmode=" not in URL:
    URL = URL + "?sslmode=require"

engine = create_engine(URL, future=True)


def main():
    with engine.connect() as conn:
        # Drop all tables
        tables = inspect(engine).get_table_names()
        if tables:
            conn.execute(text("DROP TABLE IF EXISTS " + ", ".join(f'"{t}"' for t in tables) + " CASCADE;"))
        # Drop all custom enum types
        enums = conn.execute(
            text("SELECT typname FROM pg_type WHERE typtype = 'e';")
        ).fetchall()
        for (typname,) in enums:
            conn.execute(text(f'DROP TYPE IF EXISTS "{typname}" CASCADE;'))
        # Drop alembic version table if present
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
        conn.commit()
        print(f"Dropped {len(tables)} tables and {len(enums)} enum types.")


if __name__ == "__main__":
    main()
