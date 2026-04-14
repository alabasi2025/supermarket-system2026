import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()

r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

r = s.get(base+'/stocktake', verify=False)
csrf2 = re.search(r'id="csrfToken" value="([^"]+)"', r.text).group(1)

r = s.post(base+'/api/stocktake/session', json={'title':'test'}, headers={'X-CSRF-Token': csrf2}, verify=False)
session_id = r.json()['session_id']

# Test request-product with csrf_token in form data
payload = {
    'session_id': str(session_id),
    'barcode': '9999999999999',
    'product_name': 'test product',
    'category_id': '101',
    'unit': 'حبه',
    'quantity_counted': '3',
    'pack_size': '1',
    'notes': 'test',
    'csrf_token': csrf2
}
r = s.post(base+'/api/stocktake/request-product', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Request:', r.status_code, r.json())
