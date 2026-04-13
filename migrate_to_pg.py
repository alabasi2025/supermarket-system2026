# -*- coding: utf-8 -*-
import sqlite3
import psycopg2

# Connect to SQLite
sqlite_conn = sqlite3.connect('supermarket.db')
sqlite_conn.row_factory = sqlite3.Row
sqlite_cur = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    host='localhost',
    database='supermarket',
    user='postgres',
    password='774424555'
)
pg_cur = pg_conn.cursor()

# Migrate categories
print('Migrating categories...')
sqlite_cur.execute('SELECT id, name FROM categories')
for row in sqlite_cur.fetchall():
    pg_cur.execute('''
        INSERT INTO categories (id, name, is_active)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
    ''', (row['id'], row['name'], True))
pg_conn.commit()
pg_cur.execute("SELECT setval('categories_id_seq', (SELECT COALESCE(MAX(id),1) FROM categories))")
pg_conn.commit()
print('  Done')

# Migrate products
print('Migrating products...')
sqlite_cur.execute('''
    SELECT id, product_code, name, brand, barcode, category_id, unit, 
           cost_price, sell_price, min_stock, current_stock, is_active
    FROM products
''')
count = 0
for row in sqlite_cur.fetchall():
    pg_cur.execute('''
        INSERT INTO products (id, product_code, name, brand, barcode, category_id, unit,
                             cost_price, sell_price, min_stock, current_stock, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    ''', (row['id'], row['product_code'], row['name'], row['brand'], row['barcode'],
          row['category_id'], row['unit'], row['cost_price'] or 0, row['sell_price'] or 0,
          row['min_stock'] or 0, row['current_stock'] or 0, bool(row['is_active'])))
    count += 1
    if count % 1000 == 0:
        print(f'  {count} products...')
        pg_conn.commit()
pg_conn.commit()
pg_cur.execute("SELECT setval('products_id_seq', (SELECT COALESCE(MAX(id),1) FROM products))")
pg_conn.commit()
print(f'  Total: {count} products')

# Migrate product_barcodes
print('Migrating product_barcodes...')
sqlite_cur.execute('SELECT id, product_id, barcode, unit, pack_size, cost_price, sell_price FROM product_barcodes')
count = 0
for row in sqlite_cur.fetchall():
    try:
        pg_cur.execute('''
            INSERT INTO product_barcodes (id, product_id, barcode, unit, pack_size, cost_price, sell_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        ''', (row['id'], row['product_id'], row['barcode'], row['unit'], row['pack_size'] or 1,
              row['cost_price'] or 0, row['sell_price'] or 0))
        count += 1
    except Exception as e:
        pass
pg_conn.commit()
pg_cur.execute("SELECT setval('product_barcodes_id_seq', (SELECT COALESCE(MAX(id),1) FROM product_barcodes))")
pg_conn.commit()
print(f'  Total: {count} barcodes')

# Migrate users (different column names)
print('Migrating users...')
sqlite_cur.execute('SELECT id, username, password, full_name, role, must_change_password, is_active FROM users')
for row in sqlite_cur.fetchall():
    pg_cur.execute('''
        INSERT INTO users (id, username, password_hash, display_name, role, must_change_password, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    ''', (row['id'], row['username'], row['password'], row['full_name'],
          row['role'], bool(row['must_change_password']), bool(row['is_active'])))
pg_conn.commit()
pg_cur.execute("SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id),1) FROM users))")
pg_conn.commit()
print('  Done')

# Migrate suppliers
print('Migrating suppliers...')
try:
    sqlite_cur.execute('SELECT * FROM suppliers LIMIT 1')
    cols = [d[0] for d in sqlite_cur.description]
    print(f'  Supplier columns: {cols}')
    sqlite_cur.execute('SELECT id, name, phone FROM suppliers')
    for row in sqlite_cur.fetchall():
        pg_cur.execute('''
            INSERT INTO suppliers (id, name, phone, is_active)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        ''', (row['id'], row['name'], row.get('phone', ''), True))
    pg_conn.commit()
    pg_cur.execute("SELECT setval('suppliers_id_seq', (SELECT COALESCE(MAX(id),1) FROM suppliers))")
    pg_conn.commit()
    print('  Done')
except Exception as e:
    print(f'  Skipped: {e}')

print('')
print('=== Migration Complete ===')

# Verify
pg_cur.execute('SELECT COUNT(*) FROM categories')
print(f'Categories: {pg_cur.fetchone()[0]}')
pg_cur.execute('SELECT COUNT(*) FROM products')
print(f'Products: {pg_cur.fetchone()[0]}')
pg_cur.execute('SELECT COUNT(*) FROM product_barcodes')
print(f'Barcodes: {pg_cur.fetchone()[0]}')
pg_cur.execute('SELECT COUNT(*) FROM users')
print(f'Users: {pg_cur.fetchone()[0]}')

pg_conn.close()
sqlite_conn.close()
