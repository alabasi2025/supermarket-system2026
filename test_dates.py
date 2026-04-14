import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()

# login
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True)

# stocktake page
r=s.get(base+'/stocktake', verify=False)
csrf2=re.search(r'id="csrfToken" value="([^"]+)"', r.text).group(1)

# start session
r=s.post(base+'/api/stocktake/session', json={'title':'test dates'}, headers={'X-CSRF-Token': csrf2}, verify=False)
session_id=r.json()['session_id']

# scan
barcode='6281007032582'
r=s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':barcode}, headers={'X-CSRF-Token': csrf2}, verify=False)
product=r.json()['product']

# test without dates
payload={
    'session_id': str(session_id),
    'product_id': str(product['id']),
    'barcode': barcode,
    'product_name': product['name'],
    'selected_unit': 'حبه',
    'pack_size': '1',
    'counted_stock': '5',
    'expected_stock': '0',
    'batch_no': 'BATCH-1',
    'notes': 'test'
}
r=s.post(base+'/api/stocktake/save-item', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Without dates:', r.status_code, r.json())

# test with production only
payload['production_date'] = '2025-01-01'
r=s.post(base+'/api/stocktake/save-item', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Production only:', r.status_code, r.json())

# test with both dates
payload['expiry_date'] = '2026-01-01'
r=s.post(base+'/api/stocktake/save-item', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
print('With both dates:', r.status_code, r.json())
