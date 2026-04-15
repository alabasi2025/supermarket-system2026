# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SELECT id, name FROM suppliers WHERE name LIKE '%تجربة%'")
rows = cur.fetchall()
for r in rows:
    print(f"Deleting: {r['id']} - {r['name']}")
    cur.execute("DELETE FROM supplier_phones WHERE supplier_id = %s", (r['id'],))
    cur.execute("DELETE FROM supplier_accounts WHERE supplier_id = %s", (r['id'],))
    cur.execute("DELETE FROM suppliers WHERE id = %s", (r['id'],))
conn.commit()
print(f'Deleted {len(rows)} test suppliers')
conn.close()
