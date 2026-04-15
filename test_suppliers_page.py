# -*- coding: utf-8 -*-
import requests, urllib3, re, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
s = requests.Session()
r = s.get('https://localhost:5555/login', verify=False)
m = re.search(r'csrf_token.*?value="([^"]+)"', r.text)
csrf = m.group(1) if m else ''
s.post('https://localhost:5555/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False)
r = s.get('https://localhost:5555/suppliers', verify=False)
print('Status:', r.status_code)
if r.status_code != 200:
    print('Body:', r.text[:500])
else:
    print('OK - has الموردين:', 'الموردين' in r.text)
