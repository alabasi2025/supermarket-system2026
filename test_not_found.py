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
if not m:
    m = re.search(r'content="([^"]+)".*?csrf', r.text, re.IGNORECASE)
csrf2 = m.group(1)

# start session
r = s.post(base+'/api/stocktake/session', json={'title':'test not found'}, headers={'X-CSRF-Token': csrf2}, verify=False)
session_id = r.json()['session_id']
print('Session:', session_id)

# scan non-existent barcode
barcode = '9999999999999'
r = s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':barcode}, headers={'X-CSRF-Token': csrf2}, verify=False)
data = r.json()
print('Scan:', r.status_code, 'found:', data.get('found'))

# submit request for new product
payload = {
    'session_id': str(session_id),
    'barcode': barcode,
    'product_name': 'صنف تجريبي جديد',
    'category_id': '101',
    'unit': 'حبه',
    'quantity_counted': '3',
    'pack_size': '1',
    'production_date': '2025-06-01',
    'expiry_date': '2026-06-01',
    'batch_no': 'NEW-1',
    'cost_price': '100',
    'sell_price': '120',
    'notes': 'صنف جديد من الجرد'
}
r = s.post(base+'/api/stocktake/request-product', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Request:', r.status_code)
try:
    print('JSON:', r.json())
except:
    print('Text:', r.text[:300])
