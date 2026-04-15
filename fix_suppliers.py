# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Show columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'suppliers' ORDER BY ordinal_position")
cols = [r['column_name'] for r in cur.fetchall()]
print('Columns:', cols)

# Add missing columns
for col, typ in [('notes', 'TEXT'), ('latitude', 'DOUBLE PRECISION'), ('longitude', 'DOUBLE PRECISION')]:
    if col not in cols:
        cur.execute(f"ALTER TABLE suppliers ADD COLUMN {col} {typ}")
        print(f'Added: {col}')

# Check supplier_phones
cur.execute("SELECT to_regclass('supplier_phones')")
if not cur.fetchone()['to_regclass']:
    cur.execute('''CREATE TABLE supplier_phones (
        id SERIAL PRIMARY KEY,
        supplier_id INTEGER REFERENCES suppliers(id),
        phone VARCHAR(50),
        label VARCHAR(50) DEFAULT 'جوال',
        is_primary INTEGER DEFAULT 0
    )''')
    print('Created: supplier_phones')

# Check supplier_accounts
cur.execute("SELECT to_regclass('supplier_accounts')")
if not cur.fetchone()['to_regclass']:
    cur.execute('''CREATE TABLE supplier_accounts (
        id SERIAL PRIMARY KEY,
        supplier_id INTEGER REFERENCES suppliers(id),
        account_name VARCHAR(200),
        account_number VARCHAR(100),
        notes TEXT
    )''')
    print('Created: supplier_accounts')

conn.commit()
print('Done!')
conn.close()
