import requests, re, urllib3
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

r = s.get(base+'/stocktake/requests', verify=False)
print('Requests page:', r.status_code)
print('Has pending:', 'قيد المراجعة' in r.text)
print('Has approve btn:', 'approveRequest' in r.text)
print('Has link btn:', 'showLinkModal' in r.text)
