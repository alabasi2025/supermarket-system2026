import requests, re, urllib3
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)
r = s.get(base+'/products', verify=False)
print('Products page:', r.status_code)
print('Has unit hierarchy:', 'أصغر وحدة' in r.text or 'وحدة أساسية' in r.text or 'هيكل الوحدات' in r.text)
print('Has camera scanner:', 'scanBarcode' in r.text)
print('Has conversion:', 'pu-conv' in r.text)
print('Has is_purchase:', 'pu-purchase' in r.text)
