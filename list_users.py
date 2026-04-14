# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute('SELECT id, username, role, is_active FROM users ORDER BY id')
for r in cur.fetchall():
    status = '✅' if r['is_active'] else '❌'
    print(f"ID: {r['id']} | اسم: {r['username']} | الدور: {r['role']} | الحالة: {status}")
conn.close()
