import requests
import uuid
import time

# Wait for server
for i in range(10):
    try:
        r = requests.get('http://localhost:8000/health', timeout=2)
        if r.status_code == 200:
            print('Server ready!')
            break
    except:
        time.sleep(1)
else:
    print('Server not ready')
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