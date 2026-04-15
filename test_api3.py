# -*- coding: utf-8 -*-
import requests, json, urllib3, re, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
s = requests.Session()

# login first
r = s.get('https://localhost:5555/login', verify=False)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
csrf_token = csrf.group(1) if csrf else ''
print('Login CSRF:', csrf_token[:20] + '...')

s.post('https://localhost:5555/login', data={'username':'1','password':'1234','csrf_token':csrf_token}, verify=False)

# Now go to suppliers page to get fresh CSRF
r = s.get('https://localhost:5555/suppliers', verify=False)
csrf = re.search(r'name="csrf-token" content="([^"]+)"', r.text)
csrf_token = csrf.group(1) if csrf else ''
print('Suppliers CSRF:', csrf_token[:20] + '...')

# try to add supplier
r = s.post('https://localhost:5555/api/suppliers', 
    json={'name': 'مورد تجربة', 'phone': '777', 'address': '', 'phones': [], 'accounts': []},
    headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token},
    verify=False)
print('Status:', r.status_code)
print('Response:', r.text[:500])
