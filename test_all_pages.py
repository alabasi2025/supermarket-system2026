import requests, urllib3, re, json
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
BASE = 'https://localhost:5555'

# Login
r = s.get(BASE + '/login', timeout=10)
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
csrf = m.group(1) if m else ''
r = s.post(BASE + '/login', data={'csrf_token': csrf, 'username': '1', 'password': 'admin', 'next': ''}, allow_redirects=True, timeout=10)

pages = [
    ('/', 'Main'),
    ('/dashboard', 'Dashboard'),
    ('/products', 'Products'),
    ('/categories', 'Categories'),
    ('/suppliers', 'Suppliers'),
    ('/supplier-products', 'SupplierProducts'),
    ('/supplier-invoices', 'SupplierInvoices'),
    ('/supplier-invoices/new', 'NewInvoice'),
    ('/warehouses', 'Warehouses'),
    ('/internal-transfers', 'Transfers'),
    ('/warehouse', 'Warehouse'),
    ('/inventory', 'Inventory'),
    ('/agent-invoices', 'AgentInvoices'),
    ('/pricing', 'Pricing'),
    ('/competitor-prices', 'Competitors'),
    ('/users', 'Users'),
    ('/units', 'Units'),
    ('/batches', 'Batches'),
    ('/employees', 'Employees'),
    ('/reports', 'Reports'),
    ('/settings', 'Settings'),
    ('/pos', 'POS'),
    ('/stocktake', 'Stocktake'),
    ('/chat', 'Chat'),
    ('/permissions', 'Permissions'),
]

results = []
ok = 0
fail = 0
for path, name in pages:
    try:
        r = s.get(BASE + path, timeout=15, allow_redirects=True)
        at_login = '/login' in r.url
        has_err = r.status_code >= 400 or 'Internal Server Error' in r.text
        is_ok = r.status_code == 200 and not at_login and not has_err
        if is_ok:
            ok += 1
        else:
            fail += 1
        results.append({
            'name': name,
            'path': path,
            'status': r.status_code,
            'ok': is_ok,
            'size': len(r.content),
            'at_login': at_login
        })
    except Exception as e:
        fail += 1
        results.append({'name': name, 'path': path, 'error': str(e)})

# Test APIs
api_tests = []
apis = [
    ('GET', '/api/products/search?q=عسل', 'ProductSearch'),
    ('GET', '/api/warehouses-crud', None),
    ('GET', '/api/internal-transfers/1/items', None),
]
# Only test simple GETs
for method, url, name in apis:
    try:
        r = s.get(BASE + url, timeout=10)
        api_tests.append({'url': url, 'status': r.status_code})
    except Exception as e:
        api_tests.append({'url': url, 'error': str(e)})

output = {
    'ok': ok,
    'fail': fail,
    'total': ok + fail,
    'pages': results,
    'api_tests': api_tests
}

with open('D:/supermarket-system/web/test_all_results.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
