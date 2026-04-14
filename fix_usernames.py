# -*- coding: utf-8 -*-
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# نقل الاسم الحالي إلى display_name ثم نجعل username = id
cur.execute("SELECT id, username FROM users ORDER BY id")
for r in cur.fetchall():
    cur.execute("UPDATE users SET display_name = %s, username = %s WHERE id = %s", (r[1], str(r[0]), r[0]))

conn.commit()

cur.execute("SELECT id, username, display_name, role FROM users ORDER BY id")
for r in cur.fetchall():
    print(f"ID: {r[0]} | اسم الدخول: {r[1]} | الاسم الظاهر: {r[2]} | الدور: {r[3]}")

conn.close()
