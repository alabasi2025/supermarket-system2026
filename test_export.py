import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()

# login
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True)

# export excel
r=s.get(base+'/stocktake/export/2', verify=False)
print('Export status:', r.status_code)
print('Content-Type:', r.headers.get('Content-Type'))
print('Content-Disposition:', r.headers.get('Content-Disposition'))
print('File size:', len(r.content), 'bytes')

# save to check
with open('test_export.xlsx', 'wb') as f:
    f.write(r.content)
print('Saved to test_export.xlsx')
