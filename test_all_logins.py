# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'

users = ['مدير النظام', 'أنس', 'محمد المجهلي', 'العباسي', 'خالد هبري', 'صدام العتواني', 'أبو غالب']

for u in users:
    s = requests.Session()
    r = s.get(base + '/login', verify=False, timeout=15)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
    r = s.post(base + '/login', data={'username': u, 'password': '1234', 'csrf_token': csrf}, verify=False, allow_redirects=True)
    ok = 'dashboard' in r.url
    print(f"{'✅' if ok else '❌'} {u} → {'نجح' if ok else 'فشل'}")
