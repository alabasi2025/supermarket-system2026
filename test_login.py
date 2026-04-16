import requests, urllib3, re
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
BASE = 'https://localhost:5555'

# Get CSRF
r = s.get(BASE + '/login', timeout=10)
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
csrf = m.group(1) if m else 'NONE'

# Try login with different passwords
for pwd in ['admin', '1234', '123456']:
    s2 = requests.Session()
    s2.verify = False
    r2 = s2.get(BASE + '/login', timeout=10)
    m2 = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r2.text)
    csrf2 = m2.group(1) if m2 else ''
    
    r2 = s2.post(BASE + '/login', data={
        'csrf_token': csrf2,
        'username': '1',
        'password': pwd,
        'next': ''
    }, allow_redirects=False, timeout=10)
    
    success = r2.status_code == 302
    loc = r2.headers.get('Location', 'none')
    print(f"user=1 pwd={pwd}: status={r2.status_code} redirect={loc} {'OK' if success else 'FAIL'}")
