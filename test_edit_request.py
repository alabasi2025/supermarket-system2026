import requests, re, urllib3
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

# Test page
r = s.get(base+'/stocktake/requests', verify=False)
print('Page:', r.status_code, 'Edit btn:', 'showEditModal' in r.text)

# Test edit API
r2 = s.get(base+'/stocktake/requests', verify=False)
csrf2 = re.search(r'id="csrfToken" value="([^"]+)"', r2.text).group(1)
r = s.post(base+'/api/stocktake/request/4/edit', json={'product_name':'سامي معدّل','cost_price':'50','sell_price':'60'}, headers={'X-CSRF-Token':csrf2,'Content-Type':'application/json'}, verify=False)
print('Edit:', r.status_code, r.json())
