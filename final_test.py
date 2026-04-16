# -*- coding: utf-8 -*-
import requests, urllib3, re, json
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
BASE = 'https://localhost:5555'

# Get CSRF
r = s.get(BASE + '/login', timeout=10)
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
csrf = m.group(1) if m else ''

# Login with new password
r = s.post(BASE + '/login', data={
    'csrf_token': csrf,
    'username': '1',
    'password': 'admin',
    'next': ''
}, allow_redirects=True, timeout=10)

logged_in = '/login' not in r.url

# Test all pages
pages = ['/', '/dashboard', '/products', '/categories', '/suppliers',
         '/supplier-invoices', '/agent-invoices', '/pricing', '/competitor-prices',
         '/inventory', '/users', '/units', '/batches', '/employees', '/reports',
         '/settings', '/pos', '/stocktake', '/chat', '/products/1']

results = {'login_ok': logged_in, 'pages': []}

for path in pages:
    try:
        r = s.get(BASE + path, timeout=15, allow_redirects=True)
        at_login = '/login' in r.url
        has_error = False
        error_msg = ''
        if r.status_code == 500:
            has_error = True
            error_msg = '500 Server Error'
        elif r.status_code == 404:
            has_error = True
            error_msg = '404 Not Found'
        
        results['pages'].append({
            'path': path,
            'status': r.status_code,
            'size': len(r.content),
            'ok': r.status_code == 200 and not at_login,
            'at_login': at_login,
            'error': error_msg if has_error else None
        })
    except Exception as e:
        results['pages'].append({'path': path, 'error': str(e)})

results['ok_count'] = sum(1 for p in results['pages'] if p.get('ok'))
results['total'] = len(results['pages'])

with open('D:/supermarket-system/web/final_results.json', 'w') as f:
    json.dump(results, f, indent=2)
