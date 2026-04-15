# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)
r = s.get(base+'/stocktake/requests', verify=False)
print('Status:', r.status_code)
print('Has duplicate:', 'مكرر' in r.text)
print('Has deleteReq:', 'deleteReq' in r.text)
print('Has is_duplicate:', 'is_duplicate' in r.text)
