import subprocess
import time
import requests
import uuid

# Start server
proc = subprocess.Popen(
    ['python', 'run_server.py'],
    cwd=r'C:\Users\praji\OneDrive\Desktop\SIH\backend',
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server
for i in range(15):
    try:
        r = requests.get('http://localhost:8000/health', timeout=2)
        if r.status_code == 200:
            print('Server ready!')
            break
    except:
        time.sleep(1)
else:
    print('Server not ready')
    stdout, stderr = proc.communicate(timeout=5)
    print('STDOUT:', stdout.decode())
    print('STDERR:', stderr.decode())
    exit(1)

# Test register + login + /me flow
email = f'test{uuid.uuid4().hex[:8]}@example.com'
r = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'name': 'Test User',
    'email': email,
    'password': 'supersecret123',
    'role': 'citizen'
})
print('Register:', r.status_code, r.json())

r = requests.post('http://localhost:8000/api/v1/auth/login', data={
    'username': email,
    'password': 'supersecret123'
}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
print('Login:', r.status_code, r.json())

token = r.json()['access_token']

r = requests.get('http://localhost:8000/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
print('Me:', r.status_code, r.json())

# Clean up
proc.terminate()
proc.wait(timeout=5)