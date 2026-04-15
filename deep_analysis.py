# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("=" * 70)
print("تحليل عميق لطلبات الجرد")
print("=" * 70)

# كل التفاصيل للمكررات
dups_barcodes = ['6223012612724', '9501100040015', '5236987455846', '6281011702532', '9504000361099']

for bc in dups_barcodes:
    cur.execute("""
        SELECT id, barcode, product_name, quantity_counted, 
               production_date, expiry_date, batch_no, unit, pack_size,
               created_at
        FROM stocktake_product_requests 
        WHERE barcode = %s
        ORDER BY id
    """, (bc,))
    rows = cur.fetchall()
    print(f"\n{'='*60}")
    print(f"الباركود: {bc}")
    for r in rows:
        print(f"  ID:{r['id']} | اسم:{r['product_name']} | كمية:{r['quantity_counted']} | وحدة:{r['unit']} | عبوة:{r['pack_size']}")
        print(f"        إنتاج:{r['production_date']} | انتهاء:{r['expiry_date']} | باتش:{r['batch_no']}")
        print(f"        وقت الرفع:{r['created_at']}")

# تحليل الكميات
print(f"\n{'='*60}")
print("تحليل الكميات للمكررات:")
for bc in dups_barcodes:
    cur.execute("""
        SELECT barcode, product_name, 
               COUNT(*) as times_scanned,
               SUM(quantity_counted) as total_qty,
               MIN(quantity_counted) as min_qty,
               MAX(quantity_counted) as max_qty
        FROM stocktake_product_requests 
        WHERE barcode = %s
        GROUP BY barcode, product_name
    """, (bc,))
    r = cur.fetchone()
    if r:
        print(f"  {bc} | مسح {r['times_scanned']}x | المجموع:{r['total_qty']} | أقل:{r['min_qty']} | أكثر:{r['max_qty']}")

# فرق التواريخ بين المكررات
print(f"\n{'='*60}")
print("هل التواريخ متطابقة أم مختلفة في المكررات؟")
for bc in dups_barcodes:
    cur.execute("""
        SELECT COUNT(DISTINCT expiry_date) as diff_expiry,
               COUNT(DISTINCT production_date) as diff_prod,
               COUNT(DISTINCT batch_no) as diff_batch
        FROM stocktake_product_requests 
        WHERE barcode = %s
    """, (bc,))
    r = cur.fetchone()
    same_exp = "نفس التاريخ" if r['diff_expiry'] == 1 else f"{r['diff_expiry']} تواريخ مختلفة"
    same_batch = "نفس الباتش" if r['diff_batch'] == 1 else f"{r['diff_batch']} باتشات مختلفة"
    print(f"  {bc}: انتهاء={same_exp} | باتش={same_batch}")

conn.close()
