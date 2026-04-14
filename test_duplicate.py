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

# start new session
r=s.post(base+'/api/stocktake/session', json={'title':'test duplicate'}, headers={'X-CSRF-Token': csrf2}, verify=False)
session_id=r.json()['session_id']
print('Session:', session_id)

# scan barcode
barcode='6281007061261'
r=s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':barcode}, headers={'X-CSRF-Token': csrf2}, verify=False)
product=r.json()['product']
print('Product:', product['name'])

# save first time
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
    'notes': 'first save'
}
r=s.post(base+'/api/stocktake/save-item', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
print('First save:', r.status_code, r.json())

# try save same product again
payload['counted_stock'] = '10'
payload['batch_no'] = 'BATCH-2'
r=s.post(base+'/api/stocktake/save-item', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Second save:', r.status_code, r.json())
