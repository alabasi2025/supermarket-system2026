import requests, re, urllib3
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)
r = s.get(base+'/stocktake', verify=False)
print('Stocktake page:', r.status_code)
print('Has searchBarcode:', 'searchBarcode' in r.text)
print('Has processBarcode:', 'processBarcode' in r.text)
print('Has currentSessionId:', 'currentSessionId' in r.text)
# Check if session is set
import re as re2
m = re2.search(r'let currentSessionId\s*=\s*(\d+|null)', r.text)
print('currentSessionId value:', m.group(1) if m else 'not found')
