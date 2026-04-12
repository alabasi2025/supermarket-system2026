# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('supermarket.db')
c = conn.cursor()

print("🔄 تحديث قاعدة البيانات...")

# إضافة الأعمدة الجديدة لجدول supplier_products
new_columns = [
    ('supplier_barcode', 'TEXT'),
    ('supplier_unit', "TEXT DEFAULT 'كرتون'"),
    ('purchase_price', 'REAL DEFAULT 0'),
    ('min_order_qty', 'INTEGER DEFAULT 1'),
    ('is_active', 'INTEGER DEFAULT 1'),
]

for col_name, col_type in new_columns:
    try:
        c.execute(f"ALTER TABLE supplier_products ADD COLUMN {col_name} {col_type}")
        print(f"✅ تم إضافة: {col_name}")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print(f"⏭️ موجود: {col_name}")
        else:
            print(f"❌ خطأ في {col_name}: {e}")

conn.commit()
conn.close()

print("\n✅ تم تحديث قاعدة البيانات!")
