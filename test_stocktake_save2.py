import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()
# login
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True, timeout=15)
# stocktake page + csrf
r=s.get(base+'/stocktake', verify=False, timeout=15)
csrf2=re.search(r'id="csrfToken" value="([^"]+)"', r.text).group(1)
print('csrf2 ok', bool(csrf2))
# create session
r=s.post(base+'/api/stocktake/session', json={'title':'اختبار جرد آلي'}, headers={'X-CSRF-Token': csrf2}, verify=False, timeout=15)
print('session', r.status_code, r.text)
session_id=r.json()['session_id']
# scan
barcode='6281007061261'
r=s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':barcode}, headers={'X-CSRF-Token': csrf2}, verify=False, timeout=15)
print('scan', r.status_code, r.text[:300])
obj=r.json(); product=obj['product']; unit=obj['units'][0]
# save item
payload={
 'session_id': str(session_id),
 'product_id': str(product['id']),
 'barcode': barcode,
 'product_name': product['name'],
 'selected_unit': unit['unit'],
 'pack_size': str(unit.get('pack_size') or 1),
 'counted_stock': '3',
 'expected_stock': str(product.get('current_stock') or 0),
 'production_date': '',
 'expiry_date': '',
 'batch_no': 'TEST-BATCH',
 'notes': 'اختبار حفظ من السكربت'
}
r=s.post(base+'/api/stocktake/save-item', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False, timeout=15)
print('save', r.status_code, r.text)
