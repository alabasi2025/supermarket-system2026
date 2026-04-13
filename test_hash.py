# -*- coding: utf-8 -*-
import psycopg2, psycopg2.extras
from werkzeug.security import check_password_hash

conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres',
                        password='774424555', cursor_factory=psycopg2.extras.RealDictCursor)
cur = conn.cursor()
cur.execute("SELECT password_hash FROM users WHERE username='1'")
row = cur.fetchone()
h = row['password_hash']
print(f'Hash: {h[:50]}...')
print(f'Check admin: {check_password_hash(h, "admin")}')
print(f'Check 1234: {check_password_hash(h, "1234")}')
conn.close()
