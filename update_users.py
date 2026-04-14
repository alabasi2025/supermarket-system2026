# -*- coding: utf-8 -*-
import psycopg2
from werkzeug.security import generate_password_hash

conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# تحديث المستخدمين الموجودين
cur.execute("UPDATE users SET username = 'أنس' WHERE id = 2")
cur.execute("UPDATE users SET username = 'محمد المجهلي' WHERE id = 3")
cur.execute("UPDATE users SET username = 'العباسي' WHERE id = 4")

# إضافة المستخدمين الجدد
password_hash = generate_password_hash('admin')

cur.execute("INSERT INTO users (username, password_hash, role, is_active) VALUES (%s, %s, 'manager', TRUE)", ('خالد هبري', password_hash))
cur.execute("INSERT INTO users (username, password_hash, role, is_active) VALUES (%s, %s, 'manager', TRUE)", ('صدام العتواني', password_hash))
cur.execute("INSERT INTO users (username, password_hash, role, is_active) VALUES (%s, %s, 'manager', TRUE)", ('أبو غالب', password_hash))

# تحديث صلاحيات الجميع لمدير
cur.execute("UPDATE users SET role = 'manager'")

conn.commit()

# عرض النتيجة
import sys
sys.stdout.reconfigure(encoding='utf-8')
cur.execute("SELECT id, username, role, is_active FROM users ORDER BY id")
for r in cur.fetchall():
    print(f"ID: {r[0]} | {r[1]} | {r[2]} | {'نشط' if r[3] else 'معطل'}")

conn.close()
