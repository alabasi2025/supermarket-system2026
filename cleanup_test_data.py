# -*- coding: utf-8 -*-
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor()

# إحصائيات قبل التنظيف
print("=== قبل التنظيف ===")
for table in ['stocktake_items', 'stocktake_product_requests', 'stocktake_edit_requests', 'stocktake_sessions', 'general_requests', 'chat_messages']:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table}: {cur.fetchone()[0]}")

# تنظيف
cur.execute("DELETE FROM stocktake_items")
print(f"\nحذف stocktake_items: {cur.rowcount}")

cur.execute("DELETE FROM stocktake_product_requests")
print(f"حذف stocktake_product_requests: {cur.rowcount}")

cur.execute("DELETE FROM stocktake_edit_requests")
print(f"حذف stocktake_edit_requests: {cur.rowcount}")

cur.execute("DELETE FROM stocktake_sessions")
print(f"حذف stocktake_sessions: {cur.rowcount}")

cur.execute("DELETE FROM general_requests")
print(f"حذف general_requests: {cur.rowcount}")

cur.execute("DELETE FROM chat_messages")
print(f"حذف chat_messages: {cur.rowcount}")

# إعادة تعيين التسلسلات
for seq in ['stocktake_items_id_seq', 'stocktake_product_requests_id_seq', 'stocktake_edit_requests_id_seq', 'stocktake_sessions_id_seq', 'general_requests_id_seq', 'chat_messages_id_seq']:
    try:
        cur.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1")
    except:
        conn.rollback()

conn.commit()

# إحصائيات بعد التنظيف
print("\n=== بعد التنظيف ===")
for table in ['stocktake_items', 'stocktake_product_requests', 'stocktake_edit_requests', 'stocktake_sessions', 'general_requests', 'chat_messages']:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table}: {cur.fetchone()[0]}")

conn.close()
print("\n✅ تم تنظيف كل البيانات التجريبية!")
