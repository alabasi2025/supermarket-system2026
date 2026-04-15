# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("=" * 60)
print("فحص كل خطوة من الخطة")
print("=" * 60)

# 1) الجرد
cur.execute("SELECT COUNT(*) as c FROM stocktake_sessions WHERE status = 'open'")
open_sessions = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM stocktake_items")
items_count = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM stocktake_product_requests WHERE status = 'pending'")
pending_requests = cur.fetchone()['c']
print(f"\n1) الجرد:")
print(f"   جلسات مفتوحة: {open_sessions}")
print(f"   أصناف مجرودة: {items_count}")
print(f"   طلبات أصناف جديدة: {pending_requests}")
print(f"   {'✅ جاري' if open_sessions > 0 else '❌ لا توجد جلسة'}")

# 2) اعتماد الأصناف الجديدة
cur.execute("SELECT COUNT(*) as c FROM stocktake_product_requests WHERE status = 'approved'")
approved = cur.fetchone()['c']
print(f"\n2) اعتماد الأصناف الجديدة:")
print(f"   معتمد: {approved} | قيد المراجعة: {pending_requests}")
print(f"   {'✅ موجودة' if True else ''} — صفحة /stocktake/requests")

# 3) الموردين
cur.execute("SELECT COUNT(*) as c FROM suppliers")
suppliers = cur.fetchone()['c']
print(f"\n3) الموردين:")
print(f"   عدد الموردين: {suppliers}")
print(f"   {'❌ فارغ — لا يوجد موردين' if suppliers == 0 else '✅ موجود'}")

# 4) الفواتير
try:
    cur.execute("SELECT COUNT(*) as c FROM supplier_invoices")
    invoices = cur.fetchone()['c']
    print(f"\n4) الفواتير:")
    print(f"   عدد الفواتير: {invoices}")
    print(f"   {'❌ فارغ' if invoices == 0 else '✅ موجود'}")
    
    # هل الفاتورة تحدث التكلفة؟
    cur.execute("SELECT COUNT(*) as c FROM supplier_invoice_items")
    inv_items = cur.fetchone()['c']
    print(f"   بنود الفواتير: {inv_items}")
except Exception as e:
    print(f"\n4) الفواتير: خطأ — {e}")

# 5) المطابقة
print(f"\n5) مطابقة الجرد بالفواتير:")
print(f"   ❌ غير موجود — تقرير المطابقة لم يُبنَ بعد")

# 6) قائمة ما لم يُشترَ
cur.execute("SELECT COUNT(*) as c FROM products WHERE is_active = TRUE AND (cost_price IS NULL OR cost_price = 0)")
no_price = cur.fetchone()['c']
print(f"\n6) قائمة ما لم يُشترَ من قائمة صديقك:")
print(f"   أصناف بدون سعر تكلفة: {no_price}")
print(f"   ❓ يحتاج تقرير مقارنة قائمة صديقك مع الجرد")

# تحقق من ربط الفاتورة بالمخزون
print(f"\n7) تحديث المخزون من الجرد:")
cur.execute("SELECT COUNT(*) as c FROM products WHERE current_stock > 0")
with_stock = cur.fetchone()['c']
cur.execute("SELECT COUNT(*) as c FROM products WHERE current_stock = 0 AND is_active = TRUE")
zero_stock = cur.fetchone()['c']
print(f"   أصناف برصيد > 0: {with_stock}")
print(f"   أصناف برصيد = 0: {zero_stock}")
print(f"   ❌ الجرد لم يُحوَّل لمخزون بعد")

conn.close()
print("\n" + "=" * 60)
