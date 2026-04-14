# -*- coding: utf-8 -*-
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# 1) جدول الصفحات/الموديولات
cur.execute("""
CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '',
    sort_order INTEGER DEFAULT 0
)
""")

# 2) جدول الصلاحيات
cur.execute("""
CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    module_code VARCHAR(50) NOT NULL,
    can_view BOOLEAN DEFAULT FALSE,
    can_add BOOLEAN DEFAULT FALSE,
    can_edit BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, module_code)
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_user_perm_user ON user_permissions(user_id)")

# 3) إضافة الموديولات
modules = [
    ('dashboard', 'لوحة التحكم', '🏠', 1),
    ('pos', 'نقطة البيع', '💰', 2),
    ('products', 'الأصناف', '📦', 3),
    ('categories', 'الأقسام', '📂', 4),
    ('units', 'الوحدات', '📏', 5),
    ('inventory', 'المخزون', '🏪', 6),
    ('stocktake', 'الجرد', '📋', 7),
    ('barcode_scanner', 'ماسح الباركود', '📷', 8),
    ('batches', 'الدفعات', '📑', 9),
    ('suppliers', 'الموردين', '🏭', 10),
    ('supplier_products', 'أصناف الموردين', '🔗', 11),
    ('supplier_invoices', 'فواتير المورد', '🧾', 12),
    ('agent_invoices', 'فاتورة المندوب', '📄', 13),
    ('warehouse', 'استلام المخزن', '📥', 14),
    ('pricing', 'تسعيرات البيع', '🏷️', 15),
    ('supplier_prices', 'أسعار الموردين', '💲', 16),
    ('competitor_prices', 'أسعار المنافسين', '📊', 17),
    ('reports', 'التقارير', '📈', 18),
    ('users', 'المستخدمين', '👥', 19),
    ('employees', 'الموظفين', '👤', 20),
    ('stocktake_requests', 'طلبات الأصناف', '📝', 21),
    ('chat', 'الدردشة', '💬', 22),
    ('stocktake_review', 'مراجعة الجرد', '✅', 23),
]

for code, name, icon, sort in modules:
    cur.execute("""
        INSERT INTO modules (code, name, icon, sort_order) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, icon = EXCLUDED.icon, sort_order = EXCLUDED.sort_order
    """, (code, name, icon, sort))

# 4) إعطاء المدير (user 1) كل الصلاحيات
cur.execute("SELECT id FROM users")
users = cur.fetchall()

for user_row in users:
    uid = user_row[0]
    for code, name, icon, sort in modules:
        cur.execute("""
            INSERT INTO user_permissions (user_id, module_code, can_view, can_add, can_edit, can_delete)
            VALUES (%s, %s, TRUE, TRUE, TRUE, TRUE)
            ON CONFLICT (user_id, module_code) DO NOTHING
        """, (uid, code))

conn.commit()

# عرض النتيجة
cur.execute("SELECT COUNT(*) FROM modules")
print(f"Modules: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM user_permissions")
print(f"Permissions: {cur.fetchone()[0]}")
cur.execute("SELECT u.id, u.username, COALESCE(u.display_name, u.username), COUNT(p.id) FROM users u LEFT JOIN user_permissions p ON p.user_id = u.id GROUP BY u.id, u.username, u.display_name ORDER BY u.id")
for r in cur.fetchall():
    print(f"  User {r[0]} ({r[2]}): {r[3]} permissions")

conn.close()
print("\nDone!")
