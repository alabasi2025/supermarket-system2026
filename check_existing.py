# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

pages = [
    '/suppliers', '/supplier-products', '/supplier-invoices',
    '/supplier-prices', '/warehouse', '/agent-invoices',
    '/pricing', '/inventory', '/reports', '/batches'
]

print("=== الصفحات الموجودة ===")
for page in pages:
    r = s.get(base+page, verify=False, timeout=15)
    print(f"  {r.status_code} {page}")
    if r.status_code == 200:
        # Check if has add functionality
        has_add = 'إضافة' in r.text or 'جديد' in r.text or 'add' in r.text.lower()
        print(f"       فيه إضافة: {'نعم' if has_add else 'لا'}")
