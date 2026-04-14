# -*- coding: utf-8 -*-
import psycopg2
from werkzeug.security import generate_password_hash

conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

password_hash = generate_password_hash('1234')
cur.execute("UPDATE users SET password_hash = %s", (password_hash,))
conn.commit()

print(f"Updated {cur.rowcount} users with password: 1234")
conn.close()
