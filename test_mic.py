import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True)
# Test stocktake page loads
r=s.get(base+'/stocktake', verify=False)
print('Page status:', r.status_code)
print('Has record btn:', 'existingRecordBtn' in r.text)
