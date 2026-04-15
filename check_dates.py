# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute('''
    SELECT id, barcode, product_name, production_date, expiry_date, quantity_counted, status, created_at
    FROM stocktake_product_requests
    ORDER BY id DESC LIMIT 10
''')
for r in cur.fetchall():
    print(f"ID:{r['id']} | {r['product_name'] or 'بدون اسم'} | إنتاج:{r['production_date']} | انتهاء:{r['expiry_date']} | كمية:{r['quantity_counted']} | حالة:{r['status']}")
conn.close()
