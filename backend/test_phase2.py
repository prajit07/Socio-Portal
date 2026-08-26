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

# Create a citizen user
email = f'test{uuid.uuid4().hex[:8]}@example.com'
r = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'name': 'Test Citizen',
    'email': email,
    'password': 'supersecret123',
    'role': 'citizen'
})
print('Register Citizen:', r.status_code, r.json())
citizen_id = r.json()['id']

# Login as citizen
r = requests.post('http://localhost:8000/api/v1/auth/login', data={
    'username': email,
    'password': 'supersecret123'
}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
print('Login Citizen:', r.status_code)
citizen_token = r.json()['access_token']
citizen_headers = {'Authorization': f'Bearer {citizen_token}'}

# Submit a problem
r = requests.post('http://localhost:8000/api/v1/problems', json={
    'title': 'Garbage accumulation in park',
    'description': 'There is a lot of garbage accumulating in the community park near my house. It smells bad and attracts pests.',
    'evidence_urls': ['https://example.com/photo1.jpg'],
    'evidence_text': 'Voice recording transcribed: The park has been dirty for weeks.',
    'latitude': 28.6139,
    'longitude': 77.2090,
    'address': 'Community Park, Sector 12, Dwarka, New Delhi',
    'tags': ['garbage', 'park', 'sanitation', 'community']
}, headers=citizen_headers)
print('Create Problem:', r.status_code, r.json())
problem_id = r.json()['id']

# List problems
r = requests.get('http://localhost:8000/api/v1/problems', headers=citizen_headers)
print('List Problems:', r.status_code, r.json())

# Get problem
r = requests.get(f'http://localhost:8000/api/v1/problems/{problem_id}', headers=citizen_headers)
print('Get Problem:', r.status_code, r.json())

# Create a student user
email2 = f'test{uuid.uuid4().hex[:8]}@example.com'
r = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'name': 'Test Student',
    'email': email2,
    'password': 'supersecret123',
    'role': 'student'
})
print('Register Student:', r.status_code, r.json())
student_id = r.json()['id']

# Login as student
r = requests.post('http://localhost:8000/api/v1/auth/login', data={
    'username': email2,
    'password': 'supersecret123'
}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
print('Login Student:', r.status_code)
student_token = r.json()['access_token']
student_headers = {'Authorization': f'Bearer {student_token}'}

# Student lists all problems (HEI users can see all)
r = requests.get('http://localhost:8000/api/v1/problems', headers=student_headers)
print('Student List Problems:', r.status_code, r.json())

# Student submits a solution
r = requests.post(f'http://localhost:8000/api/v1/problems/{problem_id}/solutions', json={
    'title': 'Community clean-up drive',
    'description': 'Organize weekly community clean-up drives with volunteers from local colleges.',
    'approach': 'Mobilize NSS volunteers from nearby colleges for weekly clean-up. Provide gloves, bags, and transport.',
    'tech_stack': ['Mobile app for coordination', 'WhatsApp groups'],
    'estimated_timeline': '3 months',
    'estimated_budget': '50000 INR',
    'github_url': 'https://github.com/example/cleanup',
    'demo_url': 'https://cleanup.example.com',
}, headers=student_headers)
print('Create Solution:', r.status_code, r.json())
solution_id = r.json()['id']

# List solutions
r = requests.get(f'http://localhost:8000/api/v1/problems/{problem_id}/solutions', headers=citizen_headers)
print('List Solutions:', r.status_code, r.json())

# AI Categorize (requires admin/HEI role)
# Create admin for testing
email3 = f'test{uuid.uuid4().hex[:8]}@example.com'
r = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'name': 'Test Admin',
    'email': email3,
    'password': 'supersecret123',
    'role': 'admin'
})
print('Register Admin:', r.status_code, r.json())

r = requests.post('http://localhost:8000/api/v1/auth/login', data={
    'username': email3,
    'password': 'supersecret123'
}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
print('Login Admin:', r.status_code)
admin_token = r.json()['access_token']
admin_headers = {'Authorization': f'Bearer {admin_token}'}

# AI Categorize
r = requests.post(f'http://localhost:8000/api/v1/problems/{problem_id}/categorize', headers=admin_headers)
print('AI Categorize:', r.status_code, r.json())

# Clean up
proc.terminate()
proc.wait(timeout=5)