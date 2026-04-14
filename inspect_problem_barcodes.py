import psycopg2, psycopg2.extras, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
for bc in ['6281102101848','0725765818645']:
    print('\n===', bc, '===')
    cur.execute('''
        SELECT pb.*, p.id as product_id, p.name, p.barcode as main_barcode, p.unit as main_unit,
               p.cost_price as main_cost, p.sell_price as main_sell, c.name as category_name
        FROM product_barcodes pb
        JOIN products p ON p.id = pb.product_id
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE pb.barcode = %s
    ''', (bc,))
    rows = cur.fetchall()
    print('count=', len(rows))
    for r in rows:
        print(dict(r))
conn.close()
