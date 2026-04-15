# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# إجمالي الطلبات
cur.execute("SELECT COUNT(*) as c FROM general_requests")
print(f"إجمالي الطلبات: {cur.fetchone()['c']}")

# حسب النوع
cur.execute("SELECT request_type, COUNT(*) as c FROM general_requests GROUP BY request_type ORDER BY c DESC")
print("\nحسب النوع:")
for r in cur.fetchall():
    print(f"  {r['request_type']}: {r['c']}")

# حسب الحالة
cur.execute("SELECT status, COUNT(*) as c FROM general_requests GROUP BY status")
print("\nحسب الحالة:")
for r in cur.fetchall():
    print(f"  {r['status']}: {r['c']}")

# طلبات مكررة (نفس الباركود)
cur.execute("""
    SELECT barcode, COUNT(*) as c 
    FROM general_requests 
    WHERE barcode IS NOT NULL AND barcode != ''
    GROUP BY barcode 
    HAVING COUNT(*) > 1
    ORDER BY c DESC
    LIMIT 10
""")
dups = cur.fetchall()
print(f"\nطلبات مكررة بنفس الباركود: {len(dups)}")
for r in dups:
    print(f"  {r['barcode']}: {r['c']} مرات")

# طلبات إضافة صنف بدون أسعار
cur.execute("""
    SELECT COUNT(*) as c FROM general_requests 
    WHERE request_type = 'add_product' 
    AND (details IS NULL OR details = '')
""")
print(f"\nطلبات إضافة بدون تفاصيل: {cur.fetchone()['c']}")

# طلبات يمكن تطابق باركودها مع موجود
cur.execute("""
    SELECT gr.id, gr.request_type, gr.barcode, gr.title
    FROM general_requests gr
    WHERE gr.barcode IS NOT NULL 
    AND gr.barcode != ''
    AND EXISTS (
        SELECT 1 FROM products p 
        WHERE p.barcode = gr.barcode AND p.is_active = TRUE
    )
    LIMIT 10
""")
matched = cur.fetchall()
print(f"\nطلبات باركودها موجود فعلاً في النظام: {len(matched)}")
for r in matched:
    print(f"  ID:{r['id']} | {r['request_type']} | {r['barcode']} | {r['title'][:50]}")

# عينة من الطلبات الحالية
cur.execute("""
    SELECT id, request_type, title, barcode, status, priority, created_at
    FROM general_requests 
    ORDER BY id DESC LIMIT 10
""")
print(f"\nآخر 10 طلبات:")
for r in cur.fetchall():
    print(f"  ID:{r['id']} | {r['request_type']} | {r['status']} | {r['priority']} | {(r['title'] or '')[:40]}")

conn.close()
