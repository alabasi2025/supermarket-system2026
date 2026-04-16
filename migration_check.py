import psycopg2, json
conn = psycopg2.connect(dbname='supermarket', user='postgres', password='774424555', host='localhost')
cur = conn.cursor()

results = {}

# Check new tables
for t in ['warehouses', 'warehouse_stock', 'internal_transfers', 'internal_transfer_items']:
    try:
        cur.execute("SELECT COUNT(*) FROM " + t)
        cnt = cur.fetchone()[0]
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (t,))
        cols = [r[0] for r in cur.fetchall()]
        results[t] = {'exists': True, 'rows': cnt, 'columns': cols}
    except:
        conn.rollback()
        results[t] = {'exists': False}

# Check column alterations
checks = [
    ('supplier_products', 'is_kit'),
    ('supplier_invoices', 'warehouse_id'),
    ('inventory_movements', 'warehouse_id'),
    ('supplier_invoice_items', 'is_kit_item'),
    ('supplier_invoice_items', 'supplier_product_id'),
    ('supplier_invoice_items', 'unit'),
    ('supplier_invoice_items', 'conversion_factor'),
    ('supplier_invoice_items', 'base_quantity'),
    ('supplier_invoice_items', 'parent_item_id'),
]
for table, col in checks:
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s", (table, col))
    results[f'{table}.{col}'] = cur.fetchone() is not None

# Check if warehouses has data
try:
    cur.execute("SELECT id, name, type FROM warehouses ORDER BY id")
    results['warehouses_data'] = cur.fetchall()
except:
    conn.rollback()
    results['warehouses_data'] = []

# Check new templates
import os
templates_dir = 'D:/supermarket-system/web/templates'
new_templates = ['warehouses.html', 'internal_transfers.html']
for t in new_templates:
    path = os.path.join(templates_dir, t)
    results[f'template_{t}'] = os.path.exists(path)

# Check modified templates
for t in ['supplier_invoice_form.html', 'warehouse.html', 'supplier_products.html', 'inventory.html']:
    path = os.path.join(templates_dir, t)
    if os.path.exists(path):
        results[f'template_{t}'] = os.path.getsize(path)
    else:
        results[f'template_{t}'] = False

with open('D:/supermarket-system/web/migration_check.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
conn.close()
