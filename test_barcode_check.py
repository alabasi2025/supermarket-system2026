# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

barcode = '725765996602'
print(f'=== بحث عن باركود: {barcode} ===\n')

# products
cur.execute("SELECT id, name, barcode, unit, is_active FROM products WHERE barcode = %s", (barcode,))
rows = cur.fetchall()
print(f'products: {len(rows)} نتائج')
for r in rows:
    print(f"  ID:{r['id']} | {r['name']} | Unit:{r['unit']} | Active:{r['is_active']}")

# product_barcodes
cur.execute("SELECT pb.*, p.name, p.is_active FROM product_barcodes pb JOIN products p ON p.id = pb.product_id WHERE pb.barcode = %s", (barcode,))
rows = cur.fetchall()
print(f'\nproduct_barcodes: {len(rows)} نتائج')
for r in rows:
    print(f"  ID:{r['id']} | Product:{r['name']} | Unit:{r['unit']} | Active:{r['is_active']}")

# product_units
cur.execute("SELECT pu.*, p.name, p.is_active FROM product_units pu JOIN products p ON p.id = pu.product_id WHERE pu.barcode = %s", (barcode,))
rows = cur.fetchall()
print(f'\nproduct_units: {len(rows)} نتائج')
for r in rows:
    print(f"  ID:{r['id']} | Product:{r['name']} | Unit:{r['unit_name']} | Active:{r['is_active']}")

conn.close()
