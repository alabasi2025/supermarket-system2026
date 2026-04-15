# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)
r = s.get(base+'/stocktake/review/1', verify=False)
print('Status:', r.status_code)
print('Has tabs:', 'switchTab' in r.text)
print('Items section:', 'section-items' in r.text)
print('Requests section:', 'section-requests' in r.text)
print('Production date:', 'production_date' in r.text or 'الإنتاج' in r.text)
print('Expiry date:', 'expiry_date' in r.text or 'الانتهاء' in r.text)
