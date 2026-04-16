import json, psycopg2

conn = psycopg2.connect(dbname='supermarket', user='postgres', password='774424555', host='localhost')
cur = conn.cursor()

# Get ALL tables with their schemas
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r[0] for r in cur.fetchall()]

analysis = {}
for t in tables:
    # Column info
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name=%s 
        ORDER BY ordinal_position
    """, (t,))
    cols = [{'name': r[0], 'type': r[1], 'nullable': r[2], 'default': r[3]} for r in cur.fetchall()]
    
    # Row count
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    count = cur.fetchone()[0]
    
    # Foreign keys
    cur.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s
    """, (t,))
    fks = [{'column': r[0], 'ref_table': r[1], 'ref_column': r[2]} for r in cur.fetchall()]
    
    analysis[t] = {
        'columns': cols,
        'row_count': count,
        'foreign_keys': fks
    }

# Supplier-related details
supplier_tables = {}

# supplier_products schema + sample
if 'supplier_products' in analysis:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='supplier_products' ORDER BY ordinal_position")
    supplier_tables['supplier_products_schema'] = cur.fetchall()

# sorting_rules schema
if 'sorting_rules' in analysis:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='sorting_rules' ORDER BY ordinal_position")
    supplier_tables['sorting_rules_schema'] = cur.fetchall()

# supplier_invoices schema
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='supplier_invoices' ORDER BY ordinal_position")
supplier_tables['supplier_invoices_schema'] = cur.fetchall()

# supplier_invoice_items schema
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='supplier_invoice_items' ORDER BY ordinal_position")
supplier_tables['supplier_invoice_items_schema'] = cur.fetchall()

# agent_invoices schema
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='agent_invoices' ORDER BY ordinal_position")
supplier_tables['agent_invoices_schema'] = cur.fetchall()

# agent_invoice_items schema
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='agent_invoice_items' ORDER BY ordinal_position")
supplier_tables['agent_invoice_items_schema'] = cur.fetchall()

# warehouses if exists
try:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='warehouses' ORDER BY ordinal_position")
    supplier_tables['warehouses_schema'] = cur.fetchall()
except:
    pass

# inventory_movements schema
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='inventory_movements' ORDER BY ordinal_position")
supplier_tables['inventory_movements_schema'] = cur.fetchall()

# products relevant columns
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='products' ORDER BY ordinal_position")
supplier_tables['products_schema'] = cur.fetchall()

result = {
    'table_summary': {t: {'rows': analysis[t]['row_count'], 'cols': len(analysis[t]['columns'])} for t in tables},
    'supplier_related': supplier_tables,
    'full_analysis': analysis
}

with open('D:/supermarket-system/web/full_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False, default=str)

conn.close()
