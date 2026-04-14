# -*- coding: utf-8 -*-
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# 1) أعمدة جديدة في product_barcodes
for col, typ, default in [
    ('conversion_factor', 'NUMERIC(12,4)', '1'),
    ('is_purchase', 'BOOLEAN', 'FALSE'),
    ('is_sale', 'BOOLEAN', 'TRUE'),
    ('sort_order', 'INTEGER', '0'),
]:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='product_barcodes' AND column_name='{col}'")
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE product_barcodes ADD COLUMN {col} {typ} DEFAULT {default}")
        print(f"  + product_barcodes.{col}")

# 2) جدول باركودات متعددة لكل وحدة
cur.execute("""
    CREATE TABLE IF NOT EXISTS unit_barcodes (
        id SERIAL PRIMARY KEY,
        product_barcode_id INTEGER REFERENCES product_barcodes(id) ON DELETE CASCADE,
        barcode VARCHAR(100) NOT NULL,
        is_primary BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_unit_barcodes_barcode ON unit_barcodes(barcode)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_unit_barcodes_pb ON unit_barcodes(product_barcode_id)")
print("  + unit_barcodes table")

# 3) تعيين conversion_factor من pack_size الحالي
cur.execute("UPDATE product_barcodes SET conversion_factor = pack_size WHERE conversion_factor = 1 AND pack_size > 1")
print(f"  Updated conversion_factor: {cur.rowcount} rows")

# 4) نقل الباركودات الحالية إلى unit_barcodes
cur.execute("""
    INSERT INTO unit_barcodes (product_barcode_id, barcode, is_primary)
    SELECT pb.id, pb.barcode, TRUE
    FROM product_barcodes pb
    WHERE pb.barcode IS NOT NULL AND pb.barcode != ''
    AND NOT EXISTS (SELECT 1 FROM unit_barcodes ub WHERE ub.product_barcode_id = pb.id AND ub.barcode = pb.barcode)
""")
print(f"  Migrated barcodes to unit_barcodes: {cur.rowcount}")

# 5) ترتيب الوحدات حسب conversion_factor
cur.execute("""
    UPDATE product_barcodes SET sort_order = 
        CASE 
            WHEN conversion_factor <= 1 THEN 1
            WHEN conversion_factor <= 10 THEN 2
            ELSE 3
        END
""")
print(f"  Set sort_order: {cur.rowcount}")

conn.commit()

# إحصائيات
cur.execute("SELECT COUNT(*) FROM product_barcodes")
print(f"\nTotal product_barcodes: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM unit_barcodes")
print(f"Total unit_barcodes: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(DISTINCT product_id) FROM product_barcodes")
print(f"Products with units: {cur.fetchone()[0]}")

conn.close()
print("\nDone!")
