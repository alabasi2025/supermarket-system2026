import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()

# login
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True)

# stocktake review page
r=s.get(base+'/stocktake/review', verify=False)
print('Review page:', r.status_code)
print('sessions' in r.text.lower() or 'جلسات' in r.text)

# session detail page
r=s.get(base+'/stocktake/review/2', verify=False)
print('Detail page:', r.status_code)
print('items' in r.text.lower() or 'الأصناف' in r.text)

# close session API
r2=s.get(base+'/stocktake', verify=False)
csrf2=re.search(r'id="csrfToken" value="([^"]+)"', r2.text).group(1)
r=s.post(base+'/api/stocktake/session/close', json={'session_id':2}, headers={'X-CSRF-Token': csrf2}, verify=False)
print('Close session:', r.status_code, r.json())
