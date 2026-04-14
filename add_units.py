# -*- coding: utf-8 -*-
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# جمع كل الوحدات المستخدمة
cur.execute("SELECT DISTINCT unit FROM product_barcodes WHERE unit IS NOT NULL AND unit != ''")
pb_units = [r[0] for r in cur.fetchall()]

cur.execute("SELECT DISTINCT unit FROM products WHERE unit IS NOT NULL AND unit != ''")
p_units = [r[0] for r in cur.fetchall()]

all_units = set(pb_units + p_units)

# الوحدات الموجودة
cur.execute("SELECT name FROM units")
existing = set(r[0] for r in cur.fetchall())

# إضافة الناقصة
added = 0
for u in sorted(all_units):
    if u not in existing:
        cur.execute("INSERT INTO units (name, is_active) VALUES (%s, TRUE)", (u,))
        print(f"  + {u}")
        added += 1

conn.commit()

print(f"\nأضفت {added} وحدة جديدة")

# عرض الكل
cur.execute("SELECT id, name, is_active FROM units ORDER BY id")
for r in cur.fetchall():
    print(f"  ID:{r[0]} | {r[1]} | {'نشط' if r[2] else 'معطل'}")

conn.close()
