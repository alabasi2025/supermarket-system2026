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

# get session
r=s.post(base+'/api/stocktake/session', json={'title':'test'}, headers={'X-CSRF-Token': csrf2}, verify=False)
session_id=r.json()['session_id']

# scan secondary barcode
barcode='6281102101848'
r=s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':barcode}, headers={'X-CSRF-Token': csrf2}, verify=False)
data=r.json()
print('SCAN', barcode)
print('found:', data.get('found'))
if data.get('found'):
    p=data['product']
    print('name:', p.get('name'))
    print('unit:', p.get('unit'))
    print('pack_size:', p.get('pack_size'))
    
    # save
    payload={
        'session_id': str(session_id),
        'product_id': str(p['id']),
        'barcode': barcode,
        'product_name': p['name'],
        'selected_unit': p.get('unit') or 'حبه',
        'pack_size': str(p.get('pack_size') or 1),
        'counted_stock': '10',
        'expected_stock': '0',
        'batch_no': 'BATCH-SECONDARY',
        'notes': 'test secondary barcode'
    }
    r=s.post(base+'/api/stocktake/save-item', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False)
    print('SAVE:', r.status_code, r.json())
