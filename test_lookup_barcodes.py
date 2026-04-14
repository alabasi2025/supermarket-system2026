import requests, re, urllib3, json
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()
# login
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True, timeout=15)
for bc in ['6281007061261','6281007032582','6281102101848','9501100046246','0725765818645']:
    r=s.get(base+'/api/barcode/'+bc, verify=False, timeout=15)
    print('\nBARCODE', bc, 'STATUS', r.status_code)
    print(r.text[:500])
