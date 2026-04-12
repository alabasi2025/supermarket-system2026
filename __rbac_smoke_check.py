from app import app

app.config['TESTING'] = True

ROLES = ['manager', 'agent', 'warehouse']

EXPECTED_DASHBOARD_LINKS = {
    'manager': {
        '/suppliers': True,
        '/categories': True,
        '/products': True,
        '/supplier-products': True,
        '/supplier-prices': True,
        '/competitor-prices': True,
        '/pricing': True,
        '/supplier-invoices': True,
        '/agent-invoices': True,
        '/supplier-invoices/new': True,
        '/warehouse': True,
        '/inventory': True,
        '/reports': True,
        '/users': True,
    },
    'agent': {
        '/suppliers': False,
        '/categories': False,
        '/products': False,
        '/supplier-products': False,
        '/supplier-prices': False,
        '/competitor-prices': False,
        '/pricing': False,
        '/supplier-invoices': True,
        '/agent-invoices': True,
        '/supplier-invoices/new': True,
        '/warehouse': False,
        '/inventory': False,
        '/reports': False,
        '/users': False,
    },
    'warehouse': {
        '/suppliers': False,
        '/categories': False,
        '/products': False,
        '/supplier-products': False,
        '/supplier-prices': False,
        '/competitor-prices': False,
        '/pricing': False,
        '/supplier-invoices': False,
        '/agent-invoices': False,
        '/supplier-invoices/new': False,
        '/warehouse': True,
        '/inventory': True,
        '/reports': False,
        '/users': False,
    },
}

EXPECTED_ROUTE_STATUS = {
    '/suppliers': {'manager': 200, 'agent': 302, 'warehouse': 302},
    '/api/suppliers': {'manager': 200, 'agent': 403, 'warehouse': 403},
    '/supplier-invoices': {'manager': 200, 'agent': 200, 'warehouse': 302},
    '/agent-invoices': {'manager': 200, 'agent': 200, 'warehouse': 302},
    '/supplier-invoices/new': {'manager': 200, 'agent': 200, 'warehouse': 302},
    '/warehouse': {'manager': 200, 'agent': 302, 'warehouse': 200},
    '/inventory': {'manager': 200, 'agent': 302, 'warehouse': 200},
    '/reports': {'manager': 200, 'agent': 302, 'warehouse': 302},
    '/users': {'manager': 200, 'agent': 302, 'warehouse': 302},
}


def set_role(client, role):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = role
        sess['username'] = role


def main():
    failures = []

    with app.test_client() as client:
        for role in ROLES:
            set_role(client, role)
            resp = client.get('/dashboard', follow_redirects=False)
            if resp.status_code != 200:
                failures.append(f"[DASHBOARD_STATUS] role={role} expected=200 actual={resp.status_code}")
                continue

            html = resp.get_data(as_text=True)
            for link, expected in EXPECTED_DASHBOARD_LINKS[role].items():
                present = f'href=\"{link}\"' in html
                if present != expected:
                    failures.append(
                        f"[DASHBOARD_LINK] role={role} link={link} expected={'present' if expected else 'hidden'} actual={'present' if present else 'hidden'}"
                    )

        for path, role_expectations in EXPECTED_ROUTE_STATUS.items():
            for role in ROLES:
                set_role(client, role)
                resp = client.get(path, follow_redirects=False)
                actual = resp.status_code
                expected = role_expectations[role]
                if actual != expected:
                    failures.append(f"[ROUTE_STATUS] role={role} path={path} expected={expected} actual={actual}")
                if expected == 302:
                    location = resp.headers.get('Location', '')
                    if '/dashboard' not in location:
                        failures.append(
                            f"[ROUTE_REDIRECT] role={role} path={path} expected_location_contains=/dashboard actual_location={location}"
                        )

    print('RBAC_SMOKE_CHECK')
    if failures:
        print('RESULT: FAIL')
        print('FAILURES:', len(failures))
        for failure in failures:
            print('-', failure)
    else:
        print('RESULT: PASS')
        print('FAILURES: 0')


if __name__ == '__main__':
    main()
