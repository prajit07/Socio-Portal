import subprocess, time, requests, sys

proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host','0.0.0.0','--port','8000'], cwd=r'C:\Users\praji\OneDrive\Desktop\SIH\backend')
for i in range(15):
    try:
        r = requests.get('http://localhost:8000/health', timeout=2)
        if r.status_code==200:
            print('health ok')
            break
    except: time.sleep(1)
else: print('health fail'); proc.terminate(); sys.exit(1)

# Simulate browser preflight / CORS request from frontend
r = requests.post('http://localhost:8000/api/v1/auth/login', data={'username':'x','password':'y'}, headers={'Origin':'http://localhost:5173','Content-Type':'application/x-www-form-urlencoded'})
print('login status', r.status_code)
print('CORS header', r.headers.get('access-control-allow-origin'))

# Check OPTIONS preflight
r = requests.options('http://localhost:8000/api/v1/auth/login', headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'})
print('OPTIONS status', r.status_code)
print('OPTIONS CORS', r.headers.get('access-control-allow-origin'))
proc.terminate()
proc.wait(timeout=5)
print('done')
