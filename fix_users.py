# -*- coding: utf-8 -*-
import psycopg2
from werkzeug.security import generate_password_hash

conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# Reset all passwords and flags
password_hash = generate_password_hash('1234')
cur.execute("UPDATE users SET password_hash = %s, must_change_password = FALSE", (password_hash,))
conn.commit()
print(f"Fixed {cur.rowcount} users")
conn.close()
