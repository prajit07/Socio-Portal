import requests
import uuid

# Create a test user
email = f'test{uuid.uuid4().hex[:8]}@example.com'
password = 'supersecret123'

r = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'name': 'Test User',
    'email': email,
    'password': password,
    'role': 'citizen'
})
print('Register:', r.status_code, r.json())

# Try login
r = requests.post('http://localhost:8000/api/v1/auth/login', data={
    'username': email,
    'password': password
}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
print('Login:', r.status_code, r.json())