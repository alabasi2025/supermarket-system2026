# -*- coding: utf-8 -*-
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS general_requests (
    id SERIAL PRIMARY KEY,
    request_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    details TEXT,
    product_id INTEGER REFERENCES products(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    barcode VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(50) DEFAULT 'pending',
    requested_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    reviewed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    notes TEXT
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_gen_req_type ON general_requests(request_type)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_gen_req_status ON general_requests(status)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_gen_req_user ON general_requests(requested_by)")

conn.commit()
print("Done! general_requests table created")
conn.close()
