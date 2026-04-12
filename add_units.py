# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('supermarket.db')
c = conn.cursor()

# إنشاء جدول الوحدات
c.execute('''
    CREATE TABLE IF NOT EXISTS units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        symbol TEXT,
        is_active INTEGER DEFAULT 1
    )
''')

# إنشاء جدول وحدات الصنف المتعددة
c.execute('''
    CREATE TABLE IF NOT EXISTS product_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        unit_id INTEGER NOT NULL,
        conversion_factor REAL DEFAULT 1,
        barcode TEXT,
        price REAL DEFAULT 0,
        is_default INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (unit_id) REFERENCES units(id),
        UNIQUE(product_id, unit_id)
    )
''')

# إضافة الوحدات الافتراضية
default_units = [
    ('قطعة', 'قطعة'),
    ('كرتون', 'كرتون'),
    ('كيلو', 'كجم'),
    ('جرام', 'جم'),
    ('لتر', 'لتر'),
    ('مل', 'مل'),
    ('باكت', 'باكت'),
    ('علبة', 'علبة'),
    ('كيس', 'كيس'),
    ('شدة', 'شدة'),
    ('صندوق', 'صندوق'),
    ('شوال', 'شوال'),
    ('درزن', 'درزن'),
    ('متر', 'م'),
    ('باليت', 'باليت'),
    ('طن', 'طن'),
]

for unit_name, symbol in default_units:
    try:
        c.execute("INSERT INTO units (name, symbol) VALUES (?, ?)", (unit_name, symbol))
        print(f"✅ تم إضافة: {unit_name}")
    except sqlite3.IntegrityError:
        print(f"⏭️ موجود: {unit_name}")

conn.commit()
conn.close()

print("\n✅ تم إنشاء جدول الوحدات وإضافة الوحدات الافتراضية!")
