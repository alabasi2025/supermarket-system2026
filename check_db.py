import sqlite3

conn = sqlite3.connect('supermarket.db')
c = conn.cursor()

print("=" * 50)
print("فحص قاعدة البيانات الفعلي")
print("=" * 50)

tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

for t in tables:
    name = t[0]
    count = c.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"{name}: {count} سجل")

print("\n" + "=" * 50)
print("البيانات الفعلية:")
print("=" * 50)

# Users
print("\n👤 المستخدمين:")
for u in c.execute("SELECT username, full_name, role FROM users").fetchall():
    print(f"  - {u[1]} ({u[0]}) - {u[2]}")

# Suppliers
print("\n🏭 الموردين:")
suppliers = c.execute("SELECT name FROM suppliers WHERE is_active=1").fetchall()
if suppliers:
    for s in suppliers:
        print(f"  - {s[0]}")
else:
    print("  ❌ لا يوجد موردين")

# Products
print("\n📦 الأصناف:")
products = c.execute("SELECT name FROM products WHERE is_active=1 LIMIT 10").fetchall()
if products:
    for p in products:
        print(f"  - {p[0]}")
    total = c.execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]
    if total > 10:
        print(f"  ... و {total - 10} أصناف أخرى")
else:
    print("  ❌ لا يوجد أصناف")

# Categories
print("\n📁 الأقسام:")
cats = c.execute("SELECT name FROM categories").fetchall()
if cats:
    for cat in cats:
        print(f"  - {cat[0]}")
else:
    print("  ❌ لا يوجد أقسام")

# Invoices
print("\n🧾 الفواتير:")
invs = c.execute("SELECT COUNT(*) FROM supplier_invoices").fetchone()[0]
print(f"  فواتير الموردين: {invs}")

conn.close()
