# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("=== تحليل طلبات الجرد ===\n")

# إجمالي
cur.execute("SELECT COUNT(*) as c FROM stocktake_product_requests")
total = cur.fetchone()['c']
print(f"إجمالي الطلبات: {total}")

# حسب الحالة
cur.execute("SELECT status, COUNT(*) as c FROM stocktake_product_requests GROUP BY status")
print("\nحسب الحالة:")
for r in cur.fetchall():
    print(f"  {r['status']}: {r['c']}")

# طلبات مكررة - نفس الباركود
cur.execute("""
    SELECT barcode, COUNT(*) as c, array_agg(id) as ids
    FROM stocktake_product_requests
    WHERE barcode IS NOT NULL AND barcode != ''
    GROUP BY barcode
    HAVING COUNT(*) > 1
    ORDER BY c DESC
    LIMIT 10
""")
dups = cur.fetchall()
print(f"\nباركودات مكررة: {len(dups)}")
for r in dups:
    print(f"  {r['barcode']}: {r['c']} مرات — IDs: {r['ids']}")

# طلبات باركودها موجود في النظام (كان يجب يظهر موجود)
cur.execute("""
    SELECT gr.id, gr.barcode, gr.product_name
    FROM stocktake_product_requests gr
    WHERE gr.barcode IS NOT NULL AND gr.barcode != ''
    AND EXISTS (
        SELECT 1 FROM products p 
        WHERE (p.barcode = gr.barcode OR p.barcode = LTRIM(gr.barcode,'0') OR '0'||p.barcode = gr.barcode)
        AND p.is_active = TRUE
    )
    LIMIT 10
""")
matched = cur.fetchall()
print(f"\nطلبات باركودها موجود في النظام: {len(matched)}")
for r in matched:
    print(f"  ID:{r['id']} | {r['barcode']} | {r['product_name']}")

# أصناف مكررة بنفس الاسم
cur.execute("""
    SELECT product_name, COUNT(*) as c
    FROM stocktake_product_requests
    WHERE product_name IS NOT NULL AND product_name != ''
    GROUP BY product_name
    HAVING COUNT(*) > 1
    ORDER BY c DESC
    LIMIT 10
""")
name_dups = cur.fetchall()
print(f"\nطلبات مكررة بنفس الاسم: {len(name_dups)}")
for r in name_dups:
    print(f"  {r['product_name']}: {r['c']} مرات")

# إحصائيات البيانات
cur.execute("SELECT COUNT(*) as c FROM stocktake_product_requests WHERE production_date IS NULL")
no_prod = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM stocktake_product_requests WHERE expiry_date IS NULL")
no_exp = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM stocktake_product_requests WHERE cost_price IS NULL OR cost_price = 0")
no_cost = cur.fetchone()['c']
print(f"\nجودة البيانات:")
print(f"  بدون تاريخ إنتاج: {no_prod}")
print(f"  بدون تاريخ انتهاء: {no_exp}")
print(f"  بدون سعر تكلفة: {no_cost}")

conn.close()
