# -*- coding: utf-8 -*-
import requests, urllib3
urllib3.disable_warnings()

base = 'https://localhost:5555'
s = requests.Session()
s.verify = False

# Login - follow redirects
r = s.post(f'{base}/login', data={'username': '1', 'password': 'admin'}, allow_redirects=True)
landed = r.url.replace(base, '')
print(f'Login: {r.status_code} -> {landed}')

# Check if we actually logged in
r2 = s.get(f'{base}/dashboard', allow_redirects=False)
print(f'Dashboard check: {r2.status_code}')
if r2.status_code == 302:
    print('ERROR: Not logged in! Session not maintained.')
    print(f'Cookies: {dict(s.cookies)}')
    exit(1)

pages = [
    '/dashboard', '/products', '/categories', '/suppliers',
    '/supplier-invoices', '/inventory', '/pricing', '/reports',
    '/users', '/units', '/employees', '/warehouse', '/batches',
    '/settings', '/supplier-prices', '/competitor-prices',
    '/maps', '/barcode-scanner',
]

ok_list = []
fail_list = []

for page in pages:
    try:
        r = s.get(f'{base}{page}', timeout=15)
        if r.status_code == 200:
            ok_list.append(page)
            print(f'  OK   {page}')
        else:
            fail_list.append((page, str(r.status_code)))
            print(f'  FAIL {page}: {r.status_code}')
    except Exception as e:
        fail_list.append((page, str(e)[:80]))
        print(f'  ERR  {page}: {str(e)[:80]}')

total = len(ok_list) + len(fail_list)
print(f'\n=== {len(ok_list)}/{total} OK, {len(fail_list)} FAIL ===')
for p, err in fail_list:
    print(f'  X {p}: {err}')
