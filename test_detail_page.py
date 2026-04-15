# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'1','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

# Get latest session
r = s.get(base+'/stocktake/review', verify=False)
# Find session IDs
import re as re2
session_ids = re2.findall(r'/stocktake/review/(\d+)', r.text)
if not session_ids:
    print('No sessions found')
else:
    sid = session_ids[0]
    print(f'Testing session: {sid}')
    r = s.get(f'{base}/stocktake/review/{sid}', verify=False)
    print(f'Status: {r.status_code}')
    
    # Check fields
    checks = [
        ('تاريخ الإنتاج', 'الإنتاج'),
        ('تاريخ الانتهاء', 'الانتهاء'),
        ('الباتش', 'batch'),
    ]
    for label, keyword in checks:
        found = keyword in r.text
        print(f'  {label}: {"موجود" if found else "غير موجود"}')
    
    # Check actual data
    from psycopg2 import connect
    import psycopg2.extras
    conn = connect(host='localhost', database='supermarket', user='postgres', password='774424555')
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT id, barcode, product_name, production_date, expiry_date, batch_no, quantity_counted FROM stocktake_product_requests WHERE session_id = %s LIMIT 5', (int(sid),))
    rows = cur.fetchall()
    print(f'\n  طلبات الجلسة {sid}: {len(rows)}')
    for row in rows:
        print(f"    {row['product_name'] or 'بدون اسم'} | إنتاج:{row['production_date']} | انتهاء:{row['expiry_date']} | باتش:{row['batch_no']}")
    conn.close()
