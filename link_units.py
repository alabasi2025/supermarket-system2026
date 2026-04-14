# -*- coding: utf-8 -*-
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# بناء خريطة الوحدات
cur.execute("SELECT id, name FROM units")
unit_map = {}
for r in cur.fetchall():
    unit_map[r[1]] = r[0]
    unit_map[r[1].strip()] = r[0]

print(f"الوحدات المتاحة: {len(unit_map)}")
for name, uid in sorted(unit_map.items(), key=lambda x: x[1]):
    print(f"  {uid}: {name}")

# فحص هل products فيه عمود unit_id
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='products' AND column_name='unit_id'")
has_unit_id = cur.fetchone()

if not has_unit_id:
    print("\nإضافة عمود unit_id في products...")
    cur.execute("ALTER TABLE products ADD COLUMN unit_id INTEGER REFERENCES units(id)")
    conn.commit()
    print("  تم ✅")

# ربط products.unit_id
print("\nربط الأصناف بالوحدات...")
cur.execute("SELECT id, unit FROM products WHERE unit IS NOT NULL AND unit != ''")
products = cur.fetchall()
linked = 0
not_found = set()
for pid, unit_name in products:
    uid = unit_map.get(unit_name) or unit_map.get(unit_name.strip())
    if uid:
        cur.execute("UPDATE products SET unit_id = %s WHERE id = %s", (uid, pid))
        linked += 1
    else:
        not_found.add(unit_name)

conn.commit()
print(f"  ربطت {linked} صنف")
if not_found:
    print(f"  وحدات غير موجودة في الجدول: {not_found}")

# فحص product_barcodes
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='product_barcodes' AND column_name='unit_id'")
has_pb_unit_id = cur.fetchone()

if not has_pb_unit_id:
    print("\nإضافة عمود unit_id في product_barcodes...")
    cur.execute("ALTER TABLE product_barcodes ADD COLUMN unit_id INTEGER REFERENCES units(id)")
    conn.commit()
    print("  تم ✅")

# ربط product_barcodes.unit_id
print("\nربط باركودات الوحدات...")
cur.execute("SELECT id, unit FROM product_barcodes WHERE unit IS NOT NULL AND unit != ''")
barcodes = cur.fetchall()
linked_pb = 0
not_found_pb = set()
for pbid, unit_name in barcodes:
    uid = unit_map.get(unit_name) or unit_map.get(unit_name.strip())
    if uid:
        cur.execute("UPDATE product_barcodes SET unit_id = %s WHERE id = %s", (uid, pbid))
        linked_pb += 1
    else:
        not_found_pb.add(unit_name)

conn.commit()
print(f"  ربطت {linked_pb} باركود")
if not_found_pb:
    print(f"  وحدات غير موجودة: {not_found_pb}")

# إحصائيات
cur.execute("SELECT COUNT(*) FROM products WHERE unit_id IS NOT NULL")
print(f"\nإحصائيات:")
print(f"  أصناف مربوطة بوحدة: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM products WHERE unit_id IS NULL AND unit IS NOT NULL AND unit != ''")
print(f"  أصناف غير مربوطة: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM product_barcodes WHERE unit_id IS NOT NULL")
print(f"  باركودات مربوطة: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM product_barcodes WHERE unit_id IS NULL AND unit IS NOT NULL AND unit != ''")
print(f"  باركودات غير مربوطة: {cur.fetchone()[0]}")

conn.close()
