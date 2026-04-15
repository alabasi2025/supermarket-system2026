# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("=" * 60)
print("تحليل شامل لقاعدة بيانات سوبر ماركت العباسي")
print("=" * 60)

# 1) الأصناف
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE")
active = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = FALSE")
inactive = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products")
total = cur.fetchone()['c']
print(f"\n📦 الأصناف:")
print(f"  إجمالي: {total}")
print(f"  فعّال: {active}")
print(f"  معطّل: {inactive}")

# 2) أصناف بدون باركود
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE AND (barcode IS NULL OR barcode = '')")
no_bc = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE AND barcode IS NOT NULL AND barcode != ''")
with_bc = cur.fetchone()['c']
print(f"\n🔖 الباركودات:")
print(f"  أصناف لها باركود: {with_bc}")
print(f"  أصناف بدون باركود: {no_bc}")

# 3) الوحدات
cur.execute("SELECT COUNT(*) as c FROM product_barcodes")
pb_total = cur.fetchone()['c']
cur.execute("SELECT COUNT(DISTINCT product_id) as c FROM product_barcodes")
products_with_units = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE AND id NOT IN (SELECT DISTINCT product_id FROM product_barcodes)")
products_no_extra = cur.fetchone()['c']
print(f"\n📏 الوحدات:")
print(f"  إجمالي الوحدات/الباركودات: {pb_total}")
print(f"  أصناف لها وحدات إضافية: {products_with_units}")
print(f"  أصناف بوحدة واحدة فقط: {products_no_extra}")

# 4) الوحدات المستخدمة
cur.execute("SELECT unit, COUNT(*) as c FROM product_barcodes WHERE unit IS NOT NULL GROUP BY unit ORDER BY c DESC")
print(f"\n📊 الوحدات المستخدمة:")
for r in cur.fetchall():
    print(f"  {r['unit']}: {r['c']}")

# 5) الأقسام
cur.execute("""
    SELECT c.name, COUNT(p.id) as cnt 
    FROM categories c 
    LEFT JOIN products p ON p.category_id = c.id AND p.is_active = TRUE 
    GROUP BY c.id, c.name 
    ORDER BY cnt DESC
""")
print(f"\n📂 الأقسام:")
for r in cur.fetchall():
    print(f"  {r['name']}: {r['cnt']} صنف")

# 6) أصناف بدون قسم
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE AND category_id IS NULL")
no_cat = cur.fetchone()['c']
print(f"\n  أصناف بدون قسم: {no_cat}")

# 7) أصناف مكررة (نفس الاسم)
cur.execute("""
    SELECT name, COUNT(*) as c 
    FROM products 
    WHERE is_active = TRUE 
    GROUP BY name 
    HAVING COUNT(*) > 1 
    ORDER BY c DESC 
    LIMIT 10
""")
dups = cur.fetchall()
print(f"\n⚠️ أصناف مكررة (نفس الاسم):")
if dups:
    for r in dups:
        print(f"  {r['name']}: {r['c']} مرات")
else:
    print("  لا يوجد مكررات")

# 8) أصناف بدون أسعار
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE AND (cost_price IS NULL OR cost_price = 0)")
no_cost = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE AND (sell_price IS NULL OR sell_price = 0)")
no_sell = cur.fetchone()['c']
print(f"\n💰 الأسعار:")
print(f"  بدون سعر تكلفة: {no_cost}")
print(f"  بدون سعر بيع: {no_sell}")

# 9) المستخدمين
cur.execute("SELECT COUNT(*) as c FROM users WHERE is_active = TRUE")
print(f"\n👥 المستخدمين: {cur.fetchone()['c']}")

# 10) الموردين
cur.execute("SELECT COUNT(*) as c FROM suppliers")
print(f"🏭 الموردين: {cur.fetchone()['c']}")

# 11) Units table
cur.execute("SELECT COUNT(*) as c FROM units WHERE is_active = TRUE")
print(f"📏 وحدات القياس: {cur.fetchone()['c']}")

print("\n" + "=" * 60)
print("انتهى التحليل")
print("=" * 60)

conn.close()
