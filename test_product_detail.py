# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

# Test product detail for a few products
for pid in [5, 1611, 2958, 100]:
    r = s.get(f'{base}/products/{pid}', verify=False, timeout=15)
    print(f'Product {pid}: {r.status_code}')
    if r.status_code >= 400:
        print(f'  Error: {r.text[:300]}')
