# -*- coding: utf-8 -*-
import requests, json, urllib3, re, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
s = requests.Session()

# login
r = s.get('https://localhost:5555/login', verify=False)
m = re.search(r'csrf_token.*?value="([^"]+)"', r.text) or re.search(r'csrf-token.*?content="([^"]+)"', r.text)
csrf = m.group(1) if m else ''
s.post('https://localhost:5555/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False)

# get fresh csrf from suppliers page
r = s.get('https://localhost:5555/suppliers', verify=False)
m = re.search(r'csrf-token.*?content="([^"]+)"', r.text) or re.search(r'csrf_token.*?value="([^"]+)"', r.text)
csrf2 = m.group(1) if m else ''
print('CSRF found:', bool(csrf2))

# add supplier
r = s.post('https://localhost:5555/api/suppliers', 
    json={'name': 'مورد تجربة 2', 'phone': '777', 'address': '', 'notes': '', 'latitude': None, 'longitude': None, 'phones': [], 'accounts': []},
    headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf2},
    verify=False)
print('Status:', r.status_code)
try:
    print('JSON:', json.dumps(r.json(), ensure_ascii=False))
except:
    print('Text:', r.text[:200])
