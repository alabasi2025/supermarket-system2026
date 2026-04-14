import requests, re, urllib3, json
urllib3.disable_warnings()
base='https://localhost:5555'
s=requests.Session()

print('='*60)
print('اختبار الجرد الكامل من البداية للنهاية')
print('='*60)

# 1) تسجيل الدخول
print('\n[1] تسجيل الدخول...')
r=s.get(base+'/login', verify=False, timeout=15)
csrf=re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
r=s.post(base+'/login', data={'username':'1','password':'admin','csrf_token':csrf}, verify=False, allow_redirects=True, timeout=15)
print('   الحالة:', 'نجح' if '/dashboard' in r.url or r.status_code==200 else 'فشل')

# 2) فتح صفحة الجرد والحصول على CSRF
print('\n[2] فتح صفحة الجرد...')
r=s.get(base+'/stocktake', verify=False, timeout=15)
csrf2=re.search(r'id="csrfToken" value="([^"]+)"', r.text).group(1)
print('   الحالة:', 'نجح' if r.status_code==200 else 'فشل')

# 3) بدء جلسة جرد جديدة
print('\n[3] بدء جلسة جرد...')
r=s.post(base+'/api/stocktake/session', json={'title':'اختبار جرد كامل'}, headers={'X-CSRF-Token': csrf2}, verify=False, timeout=15)
data=r.json()
session_id=data.get('session_id')
print('   الحالة:', 'نجح' if data.get('success') else 'فشل')
print('   رقم الجلسة:', session_id)

# 4) مسح باركود صنف موجود (باركود أساسي)
print('\n[4] مسح باركود صنف موجود (أساسي)...')
barcode='6281007061261'
r=s.post(base+'/api/stocktake/scan', json={'session_id':session_id,'barcode':barcode}, headers={'X-CSRF-Token': csrf2}, verify=False, timeout=15)
data=r.json()
print('   الباركود:', barcode)
print('   موجود؟', 'نعم' if data.get('found') else 'لا')
if data.get('found'):
    product=data['product']
    units=data.get('units',[])
    print('   اسم الصنف:', product.get('name'))
    print('   الوحدات:', [u.get('unit') for u in units])

# 5) حفظ الصنف في الجرد
print('\n[5] حفظ الصنف في قائمة الجرد...')
payload={
    'session_id': str(session_id),
    'product_id': str(product['id']),
    'barcode': barcode,
    'product_name': product['name'],
    'selected_unit': units[0]['unit'] if units else 'حبه',
    'pack_size': str(units[0].get('pack_size',1) if units else 1),
    'counted_stock': '5',
    'expected_stock': str(product.get('current_stock',0)),
    'production_date': '2026-01-15',
    'expiry_date': '2027-01-15',
    'batch_no': 'BATCH-001',
    'notes': 'اختبار حفظ كامل'
}
r=s.post(base+'/api/stocktake/save-item', data=payload, headers={'X-CSRF-Token': csrf2}, verify=False, timeout=15)
print('   HTTP Status:', r.status_code)
try:
    data=r.json()
    print('   النتيجة:', 'نجح' if data.get('success') else 'فشل')
    print('   الرسالة:', data.get('message'))
except:
    print('   الرد:', r.text[:200])

print('\n' + '='*60)
print('انتهى الاختبار')
print('='*60)
