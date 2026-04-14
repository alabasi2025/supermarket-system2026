import requests, re, urllib3
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()
# login user 1
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
r=s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=False, timeout=15)
print('login_status', r.status_code, 'location', r.headers.get('Location'))
# if redirected, follow
if r.status_code in (301,302,303):
    r=s.get(base+r.headers['Location'] if r.headers['Location'].startswith('/') else r.headers['Location'], verify=False, timeout=15)
print('after_login_url', r.url)
# stocktake page
r=s.get(base+'/stocktake', verify=False, timeout=15)
print('stocktake_url', r.url, 'status', r.status_code)
print('has csrfToken', 'id="csrfToken"' in r.text)
print(r.text[:800])
