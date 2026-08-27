@echo off
cd /d "C:\Users\praji\OneDrive\Desktop\SIH\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload