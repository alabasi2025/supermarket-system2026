# -*- coding: utf-8 -*-
import requests, urllib3
urllib3.disable_warnings()

base = 'https://localhost:5555'
s = requests.Session()
s.verify = False

print('1. POST login...')
r = s.post(base + '/login', data={'username': '1', 'password': 'admin'}, allow_redirects=False)
loc = r.headers.get('Location', 'none')
print(f'   Status: {r.status_code}, Location: {loc}')
print(f'   Cookies: {dict(s.cookies)}')

if r.status_code in (301, 302):
    print('2. Follow redirect...')
    r2 = s.get(base + loc, allow_redirects=False)
    loc2 = r2.headers.get('Location', 'none')
    print(f'   Status: {r2.status_code}, Location: {loc2}')
    print(f'   Cookies: {dict(s.cookies)}')

    if r2.status_code in (301, 302):
        print('3. Follow 2nd redirect...')
        r3 = s.get(base + loc2, allow_redirects=False)
        print(f'   Status: {r3.status_code}')

print('\n4. Direct dashboard test...')
r4 = s.get(base + '/dashboard', allow_redirects=False)
loc4 = r4.headers.get('Location', 'none')
print(f'   Status: {r4.status_code}, Location: {loc4}')
