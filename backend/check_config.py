import sys
sys.path.insert(0, '.')
from app.core.config import settings
print('DB URL:', settings.DATABASE_URL[:50] + '...')