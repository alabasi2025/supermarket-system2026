# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555', cursor_factory=psycopg2.extras.RealDictCursor)
cur = conn.cursor()
cur.execute("SELECT id, name, barcode, is_active FROM products WHERE name LIKE %s ORDER BY is_active DESC", ('%جبن مثلث سالم%',))
for r in cur.fetchall():
    status = 'ACTIVE' if r['is_active'] else 'REMOVED'
    print(f"[{status}] ID={r['id']} barcode={r['barcode'] or '-'}")
    if r['is_active']:
        cur2 = conn.cursor()
        cur2.execute('SELECT barcode, unit, pack_size, cost_price, sell_price FROM product_barcodes WHERE product_id = %s ORDER BY pack_size', (r['id'],))
        for b in cur2.fetchall():
            print(f"  -> {b['unit']}: barcode={b['barcode']} pack={b['pack_size']} cost={b['cost_price']} sell={b['sell_price']}")
conn.close()
