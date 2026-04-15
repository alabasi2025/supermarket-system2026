import requests, re, urllib3
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)
r = s.get(base+'/stocktake', verify=False)
csrf2 = re.search(r'id="csrfToken" value="([^"]+)"', r.text).group(1)

# إنشاء جلسة جرد
r = s.post(base+'/api/stocktake/session', json={'title':'الجرد الأولي الرسمي'}, headers={'X-CSRF-Token': csrf2}, verify=False)
print(r.json())
