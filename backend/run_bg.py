import subprocess
import time
import sys

# Start server
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    cwd=r'C:\Users\praji\OneDrive\Desktop\SIH\backend'
)

print("Server started. Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    proc.terminate()
    proc.wait()
    print("Server stopped.")