# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()

# login
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

# stocktake page
r = s.get(base+'/stocktake', verify=False)
m = re.search(r'id="csrfToken" value="([^"]+)"', r.text)
csrf2 = m.group(1) if m else ''
print('CSRF:', csrf2[:20])

# start session
r = s.post(base+'/api/stocktake/session', json={'title':'test'}, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Session:', r.status_code, r.text[:200])
session_id = r.json().get('session_id')

# scan non-existent barcode
barcode = '9999999999999'
r = s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':barcode}, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Scan status:', r.status_code)
print('Scan response:', r.text[:300])

if r.status_code == 200:
    data = r.json()
    print('Found:', data.get('found'))
    
    if not data.get('found'):
        # Submit request
        payload = {
            'session_id': str(session_id),
            'barcode': barcode,
            'product_name': 'test new product',
            'category_id': '101',
            'unit': 'حبه',
            'quantity_counted': '3',
            'pack_size': '1',
            'notes': 'test'
        }
        r = s.post(base+'/api/stocktake/request-product', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
        print('Request status:', r.status_code)
        print('Request response:', r.text[:300])
