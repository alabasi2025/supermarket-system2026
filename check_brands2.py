# -*- coding: utf-8 -*-
"""
تحليل الماركات (العلامات التجارية) في الملف وفي قاعدة البيانات
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl
import psycopg2, psycopg2.extras
from collections import Counter

# === قراءة أسماء الأصناف من Excel ===
path = r"C:\Users\qbas\Desktop\مجلد جديد\نسخة من اصناف_مواد_غذائية(1).xlsx"
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

names = []
ws1 = wb['Sheet1']
for row in ws1.iter_rows(min_row=2, values_only=True):
    if row[4]:
        names.append(str(row[4]).strip())
wb.close()

print("=" * 70)
print(f"تحليل الماركات من أسماء الأصناف ({len(names)} صنف)")
print("=" * 70)

# الماركات مستخرجة من أول كلمة أو كلمتين في اسم الصنف
print("\n--- الكلمة الأولى من اسم الصنف (أكثر 30 تكراراً) ---")
first_words = Counter()
for n in names:
    parts = n.split()
    if parts:
        first_words[parts[0]] += 1

for word, cnt in first_words.most_common(40):
    print(f"  {word:<30} {cnt:>5}")

print("\n\n--- أول كلمتين (أكثر 30 تكراراً) ---")
two_words = Counter()
for n in names:
    parts = n.split()
    if len(parts) >= 2:
        two_words[parts[0] + ' ' + parts[1]] += 1

for word, cnt in two_words.most_common(40):
    if cnt >= 5:
        print(f"  {word:<35} {cnt:>5}")

# === حالة DB ===
print(f"\n{'='*70}")
print("قاعدة البيانات — عمود brand الحالي")
print("=" * 70)

conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("SELECT brand, COUNT(*) as cnt FROM products WHERE is_active=TRUE AND brand IS NOT NULL AND brand != '' GROUP BY brand ORDER BY cnt DESC LIMIT 30")
print("\nأكثر 30 ماركة في DB:")
for r in cur.fetchall():
    print(f"  {r['brand']:<30} {r['cnt']:>5}")

# عينة من الأصناف بدون ماركة
cur.execute("SELECT name, brand FROM products WHERE is_active=TRUE LIMIT 20")
print("\nعينة أصناف مع الماركة المحفوظة:")
for r in cur.fetchall():
    print(f"  {r['name'][:45]:<47} brand='{r['brand'] or ''}'")

conn.close()
