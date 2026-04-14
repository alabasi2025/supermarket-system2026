# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute('''
    SELECT p.id, p.name, p.barcode, p.unit, p.cost_price, p.sell_price 
    FROM products p 
    WHERE p.name ILIKE %s AND p.is_active = TRUE
    LIMIT 10
''', ('%كمران%',))
rows = cur.fetchall()
print('=== سجاير كمران ===')
for r in rows:
    print(f"ID: {r['id']}, Name: {r['name']}, Barcode: {r['barcode']}, Unit: {r['unit']}")

# check product_barcodes for these
for row in rows:
    pid = row['id']
    cur.execute('SELECT * FROM product_barcodes WHERE product_id = %s', (pid,))
    barcodes = cur.fetchall()
    if barcodes:
        print(f"\n=== وحدات الصنف {pid} ({row['name']}) ===")
        for b in barcodes:
            print(f"  Unit: {b['unit']}, Barcode: {b['barcode']}, Pack: {b['pack_size']}, Cost: {b['cost_price']}, Sell: {b['sell_price']}")
conn.close()
