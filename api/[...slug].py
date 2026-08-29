import os
import sys

# Make the backend package importable (backend/app is the `app` package).
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from mangum import Mangum
from app.main import app

# lifespan="off" — Vercel has no startup/shutdown events; the Neon DB and
# pgvector extension are already provisioned, so we don't need the lifespan hook.
handler = Mangum(app, lifespan="off")
