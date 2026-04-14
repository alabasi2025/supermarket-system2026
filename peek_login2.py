import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()
r=s.get(base+'/login', verify=False, timeout=15)
print('has_csrf=', 'csrf_token' in r.text)
print(re.findall(r'name="([^"]+)" value="([^"]*)"', r.text)[:10])
