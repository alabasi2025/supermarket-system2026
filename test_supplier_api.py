# -*- coding: utf-8 -*-
import requests, json, urllib3, re, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
s = requests.Session()

# login
r = s.get('https://localhost:5555/login', verify=False)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post('https://localhost:5555/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False)

# try to add supplier
r = s.post('https://localhost:5555/api/suppliers', 
    json={'name': 'مورد تجربة', 'phone': '', 'address': ''},
    headers={'Content-Type': 'application/json'},
    verify=False)
print('Status:', r.status_code)
print('Response:', r.text[:500])
