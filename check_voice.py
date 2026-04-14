# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys, os
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute('SELECT id, product_name, voice_note_path FROM stocktake_items WHERE voice_note_path IS NOT NULL ORDER BY id DESC LIMIT 5')
for r in cur.fetchall():
    path = r['voice_note_path']
    full = os.path.join('D:/supermarket-system/web', path) if path else ''
    exists = os.path.exists(full) if full else False
    print(f"ID: {r['id']}, Voice: {path}, Exists: {exists}, Full: {full}")

    # check what URL would be
    print(f"  URL would be: /{path}")
conn.close()
