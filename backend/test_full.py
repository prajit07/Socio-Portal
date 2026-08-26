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

# Test register different roles
roles = ['citizen', 'student', 'faculty', 'industry', 'government', 'university_admin']
for role in roles:
    email = f'test{uuid.uuid4().hex[:8]}@example.com'
    r = requests.post('http://localhost:8000/api/v1/auth/register', json={
        'name': f'Test {role.capitalize()}',
        'email': email,
        'password': 'supersecret123',
        'role': role
    })
    print(f'Register {role}:', r.status_code, r.json())

# Clean up
proc.terminate()
proc.wait(timeout=5)