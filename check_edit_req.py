# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys, json
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute('SELECT * FROM stocktake_edit_requests ORDER BY id DESC LIMIT 3')
for r in cur.fetchall():
    print(f"ID: {r['id']}")
    print(f"  Product: {r['product_name']} ({r['barcode']})")
    print(f"  Type: {r['request_type']}")
    print(f"  Status: {r['status']}")
    details = r['details'] or ''
    print(f"  Details:")
    print(f"  {details[:500]}")
    print()
conn.close()
