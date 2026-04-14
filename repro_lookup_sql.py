import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
barcode='6281102101848'
cur.execute('''
    SELECT p.*, c.name as category_name,
           pb.unit as barcode_unit, pb.pack_size as barcode_pack_size,
           pb.cost_price as barcode_cost, pb.sell_price as barcode_sell,
           pb.barcode as matched_barcode
    FROM product_barcodes pb
    JOIN products p ON p.id = pb.product_id
    LEFT JOIN categories c ON c.id = p.category_id
    WHERE pb.barcode = %s AND p.is_active = TRUE
''', (barcode,))
row = cur.fetchone()
print(row)
print(type(row))
print(dict(row))
conn.close()
