import requests, re, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()
base = 'https://localhost:5555'
s = requests.Session()
r = s.get(base+'/login', verify=False, timeout=15)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
s.post(base+'/login', data={'username':'4','password':'1234','csrf_token':csrf}, verify=False, allow_redirects=True)

# Check review pages
r = s.get(base+'/stocktake/review', verify=False)
print('Review list:', r.status_code)

# Check detail of session that has requests
import psycopg2, psycopg2.extras
conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SELECT id, session_id, barcode, product_name, status FROM stocktake_product_requests ORDER BY id DESC LIMIT 5")
for row in cur.fetchall():
    print(f"  Request ID:{row['id']} Session:{row['session_id']} Barcode:{row['barcode']} Name:{row['product_name']} Status:{row['status']}")
conn.close()
