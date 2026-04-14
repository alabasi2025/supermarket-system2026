# -*- coding: utf-8 -*-
import psycopg2
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# Fix voice_note_path
cur.execute("UPDATE stocktake_items SET voice_note_path = 'static/' || voice_note_path WHERE voice_note_path IS NOT NULL AND voice_note_path NOT LIKE 'static/%'")
print('voice_note_path fixed:', cur.rowcount)

# Fix image_path
cur.execute("UPDATE stocktake_items SET image_path = 'static/' || image_path WHERE image_path IS NOT NULL AND image_path NOT LIKE 'static/%'")
print('image_path fixed:', cur.rowcount)

# Fix attachment_path
cur.execute("UPDATE stocktake_items SET attachment_path = 'static/' || attachment_path WHERE attachment_path IS NOT NULL AND attachment_path NOT LIKE 'static/%'")
print('attachment_path fixed:', cur.rowcount)

conn.commit()

# Verify
cur.execute("SELECT id, voice_note_path FROM stocktake_items WHERE voice_note_path IS NOT NULL")
for r in cur.fetchall():
    print(f"  ID {r[0]}: {r[1]}")

conn.close()
