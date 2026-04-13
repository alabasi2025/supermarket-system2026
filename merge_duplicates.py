# -*- coding: utf-8 -*-
"""
دمج الأصناف المكررة (بنفس الاسم) في صنف واحد
- الصنف الأول يبقى (الأقل id)
- باركودات الأصناف المكررة تنتقل إلى الأول
- الأصناف المكررة تتعطل (is_active = false)
"""
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    host='localhost', database='supermarket',
    user='postgres', password='774424555',
    cursor_factory=psycopg2.extras.RealDictCursor
)
cur = conn.cursor()

# 1. Find all duplicate groups
cur.execute("""
    SELECT name, array_agg(id ORDER BY id) as ids
    FROM products
    WHERE is_active = TRUE
    GROUP BY name
    HAVING COUNT(*) > 1
""")
groups = cur.fetchall()
print(f"Found {len(groups)} duplicate groups")

total_merged = 0
total_barcodes_moved = 0
total_barcodes_added = 0

for group in groups:
    name = group['name']
    ids = group['ids']
    keep_id = ids[0]  # Keep the first one
    remove_ids = ids[1:]  # Remove the rest
    
    # Get the keeper's existing barcodes
    cur.execute("SELECT barcode FROM product_barcodes WHERE product_id = %s", (keep_id,))
    existing_barcodes = set(row['barcode'] for row in cur.fetchall() if row['barcode'])
    
    # Also get keeper's main barcode
    cur.execute("SELECT barcode, unit, cost_price, sell_price FROM products WHERE id = %s", (keep_id,))
    keeper = cur.fetchone()
    keeper_main_barcode = keeper['barcode'] if keeper else None
    if keeper_main_barcode:
        existing_barcodes.add(keeper_main_barcode)
    
    for dup_id in remove_ids:
        # Get duplicate's info
        cur.execute("SELECT barcode, unit, cost_price, sell_price FROM products WHERE id = %s", (dup_id,))
        dup = cur.fetchone()
        
        # Move its product_barcodes to keeper
        cur.execute("""
            UPDATE product_barcodes SET product_id = %s 
            WHERE product_id = %s AND (barcode IS NULL OR barcode NOT IN (
                SELECT barcode FROM product_barcodes WHERE product_id = %s AND barcode IS NOT NULL
            ))
        """, (keep_id, dup_id, keep_id))
        moved = cur.rowcount
        total_barcodes_moved += moved
        
        # Delete remaining barcodes that are duplicates
        cur.execute("DELETE FROM product_barcodes WHERE product_id = %s", (dup_id,))
        
        # If dup has a main barcode that keeper doesn't have, add it
        if dup and dup['barcode'] and dup['barcode'] not in existing_barcodes:
            cur.execute("""
                INSERT INTO product_barcodes (product_id, barcode, unit, pack_size, cost_price, sell_price)
                VALUES (%s, %s, %s, 1, %s, %s)
            """, (keep_id, dup['barcode'], dup.get('unit', 'حبه'), 
                  dup.get('cost_price', 0), dup.get('sell_price', 0)))
            existing_barcodes.add(dup['barcode'])
            total_barcodes_added += 1
        
        # If keeper has no main barcode but dup does, update keeper
        if not keeper_main_barcode and dup and dup['barcode']:
            cur.execute("UPDATE products SET barcode = %s WHERE id = %s", (dup['barcode'], keep_id))
            keeper_main_barcode = dup['barcode']
        
        # If keeper has no cost/sell price but dup does, update keeper
        if keeper and (not keeper['cost_price'] or keeper['cost_price'] == 0) and dup and dup.get('cost_price'):
            cur.execute("UPDATE products SET cost_price = %s, sell_price = %s WHERE id = %s AND (cost_price IS NULL OR cost_price = 0)",
                       (dup['cost_price'], dup['sell_price'], keep_id))
        
        # Deactivate duplicate
        cur.execute("UPDATE products SET is_active = FALSE WHERE id = %s", (dup_id,))
        total_merged += 1
    
    # Also ensure keeper's main barcode is in product_barcodes
    if keeper_main_barcode:
        cur.execute("""
            INSERT INTO product_barcodes (product_id, barcode, unit, pack_size, cost_price, sell_price)
            SELECT %s, %s, %s, 1, %s, %s
            WHERE NOT EXISTS (SELECT 1 FROM product_barcodes WHERE product_id = %s AND barcode = %s)
        """, (keep_id, keeper_main_barcode, keeper.get('unit', 'حبه'), 
              keeper.get('cost_price', 0), keeper.get('sell_price', 0),
              keep_id, keeper_main_barcode))

conn.commit()

# Verify
cur.execute("SELECT COUNT(*) as count FROM products WHERE is_active = TRUE")
active = cur.fetchone()['count']
cur.execute("SELECT COUNT(*) as count FROM products WHERE is_active = FALSE")
inactive = cur.fetchone()['count']
cur.execute("SELECT COUNT(*) as count FROM product_barcodes")
barcodes = cur.fetchone()['count']

print(f"\n=== Done ===")
print(f"Merged: {total_merged} duplicate products")
print(f"Barcodes moved: {total_barcodes_moved}")
print(f"Barcodes added: {total_barcodes_added}")
print(f"\nActive products: {active}")
print(f"Inactive products: {inactive}")
print(f"Total barcodes: {barcodes}")

# Check remaining duplicates
cur.execute("""
    SELECT COUNT(*) as count FROM (
        SELECT name FROM products WHERE is_active = TRUE
        GROUP BY name HAVING COUNT(*) > 1
    ) x
""")
remaining = cur.fetchone()['count']
print(f"Remaining duplicate groups: {remaining}")

conn.close()
