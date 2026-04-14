import requests, re, urllib3, sys, json
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

# Scan kamran - has multiple units
r = s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':'725765996602'}, headers={'X-CSRF-Token': csrf2}, verify=False)
data = r.json()
print('Found:', data.get('found'))
print('Units:')
for u in data.get('units', []):
    print(f"  {u['unit']} | conv:{u.get('conversion_factor',1)} | barcode:{u.get('barcode','-')} | cost:{u.get('cost_price','-')} | sell:{u.get('sell_price','-')}")
