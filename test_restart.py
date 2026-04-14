import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
r=s.post(base+'/login', data={'username':'العباسي','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)
print('Login:', 'OK' if 'dashboard' in r.url else 'FAIL', r.url)
