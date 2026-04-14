import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'

tests = [('1', '1234'), ('2', '1234'), ('4', '1234'), ('7', '1234'), ('العباسي', '1234')]

for u, p in tests:
    s = requests.Session()
    r = s.get(base + '/login', verify=False, timeout=15)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
    r = s.post(base + '/login', data={'username': u, 'password': p, 'csrf_token': csrf}, verify=False, allow_redirects=True)
    ok = 'dashboard' in r.url
    print(f"{'✅' if ok else '❌'} Login '{u}' → {'نجح' if ok else 'فشل'}")
