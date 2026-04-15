# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

pages = ['/stocktake', '/products', '/dashboard', '/chat', '/requests', '/stocktake/requests', '/stocktake/review', '/permissions', '/suppliers', '/categories', '/inventory']
for page in pages:
    r = s.get(base+page, verify=False, timeout=15)
    ok = 'OK' if r.status_code == 200 else 'FAIL'
    print(f'{ok} {page}: {r.status_code}')
    if r.status_code >= 400:
        print(f'  Error: {r.text[:200]}')
