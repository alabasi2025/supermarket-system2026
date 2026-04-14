import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()

# login as user 1
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True)

# stocktake page
r=s.get(base+'/stocktake', verify=False)
m=re.search(r'id="csrfToken" value="([^"]+)"', r.text)
if not m:
    m=re.search(r'name="csrf-token" content="([^"]+)"', r.text)
if not m:
    m=re.search(r'csrf.token.*?value="([^"]+)"', r.text, re.IGNORECASE)
if not m:
    print('CSRF not found, looking for meta...')
    m=re.search(r'content="([^"]+)".*?csrf', r.text, re.IGNORECASE)
csrf2=m.group(1) if m else ''
print('CSRF:', csrf2[:20] if csrf2 else 'NOT FOUND')

# start session
r=s.post(base+'/api/stocktake/session', json={'title':'test voice'}, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Session:', r.status_code, r.text[:200])
session_id=r.json().get('session_id')

# scan
barcode='9501100046246'
r=s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':barcode}, headers={'X-CSRF-Token': csrf2}, verify=False)
data=r.json()
print('Scan:', data.get('found'))
product=data['product']

# save with voice file
import io
fake_audio = io.BytesIO(b'\x00' * 1000)
payload={
    'session_id': str(session_id),
    'product_id': str(product['id']),
    'barcode': barcode,
    'product_name': product['name'],
    'selected_unit': 'حبه',
    'pack_size': '1',
    'counted_stock': '5',
    'expected_stock': '0',
    'production_date': '2025-01-01',
    'expiry_date': '2026-01-01',
    'batch_no': 'V-1',
    'notes': 'test voice'
}
files = {
    'voice_note': ('voice.webm', fake_audio, 'audio/webm')
}
r=s.post(base+'/api/stocktake/save-item', data=payload, files=files, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Save:', r.status_code)
try:
    print('JSON:', r.json())
except:
    print('Text:', r.text[:300])
