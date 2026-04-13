# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import psycopg2, psycopg2.extras

conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print('=' * 50)
print('حالة قاعدة البيانات')
print('=' * 50)

cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE")
active = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = FALSE")
inactive = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products")
total = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM product_barcodes")
barcodes = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM categories")
cats = cur.fetchone()['c']

print(f"أصناف فعّالة:  {active}")
print(f"أصناف معطّلة:  {inactive}")
print(f"إجمالي:        {total}")
print(f"باركودات:      {barcodes}")
print(f"أقسام:         {cats}")

print()
print('=== الأسعار ===')
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active=TRUE AND sell_price IS NOT NULL AND sell_price > 0")
w_sell = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active=TRUE AND cost_price IS NOT NULL AND cost_price > 0")
w_cost = cur.fetchone()['c']
print(f"بسعر بيع:      {w_sell} / {active}")
print(f"بسعر تكلفة:    {w_cost} / {active}")
print(f"بدون بيع:      {active - w_sell}")
print(f"بدون تكلفة:    {active - w_cost}")

print()
print('=== الأقسام ===')
cur.execute("""
    SELECT c.id, c.name, COUNT(p.id) as cnt
    FROM categories c
    LEFT JOIN products p ON p.category_id = c.id AND p.is_active = TRUE
    GROUP BY c.id, c.name
    ORDER BY c.id
""")
for r in cur.fetchall():
    print(f"  {r['id']:>3} - {r['name']:<25} {r['cnt']:>5} صنف")

print()
print('=== عينة أصناف بدون تكلفة ===')
cur.execute("""
    SELECT name, barcode, sell_price, cost_price
    FROM products
    WHERE is_active = TRUE AND (cost_price IS NULL OR cost_price = 0)
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  {r['name'][:40]:<42} بيع={r['sell_price'] or 0:<10} تكلفة={r['cost_price'] or 0}")

conn.close()
