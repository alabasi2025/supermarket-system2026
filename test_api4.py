# -*- coding: utf-8 -*-
import requests, json, urllib3, re, sys, traceback
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
s = requests.Session()

r = s.get('https://localhost:5555/login', verify=False)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post('https://localhost:5555/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False)

r = s.get('https://localhost:5555/suppliers', verify=False)
csrf2 = re.search(r'name="csrf-token" content="([^"]+)"', r.text).group(1)

r = s.post('https://localhost:5555/api/suppliers', 
    json={'name': 'مورد تجربة', 'phone': '777', 'address': '', 'notes': '', 'latitude': None, 'longitude': None, 'phones': [], 'accounts': []},
    headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf2},
    verify=False)
print('Status:', r.status_code)
try:
    print('JSON:', json.dumps(r.json(), ensure_ascii=False))
except:
    print('Text:', r.text[:300])
