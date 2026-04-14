# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()

r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

r = s.get(base+'/stocktake', verify=False)
m = re.search(r'id="csrfToken" value="([^"]+)"', r.text)
csrf2 = m.group(1)

r = s.post(base+'/api/stocktake/session', json={'title':'test'}, headers={'X-CSRF-Token': csrf2}, verify=False)
session_id = r.json()['session_id']

# Test barcode lookup directly
r = s.get(base+'/api/barcode/725765996602', verify=False)
print('Direct lookup:', r.status_code)
print(r.text[:300])

# Test scan
r = s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':'725765996602'}, headers={'X-CSRF-Token': csrf2}, verify=False)
print('\nScan:', r.status_code)
print(r.text[:300])
