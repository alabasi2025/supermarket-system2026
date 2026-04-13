# -*- coding: utf-8 -*-
"""
التعرف على الماركات الحقيقية من أسماء الأصناف
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import psycopg2, psycopg2.extras

conn = psycopg2.connect(host='localhost', database='supermarket', user='postgres', password='774424555')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT p.id, p.name, p.brand, c.name as category_name, p.category_id
    FROM products p
    LEFT JOIN categories c ON c.id = p.category_id
    WHERE p.is_active = TRUE
    ORDER BY p.category_id, p.name
""")
products = cur.fetchall()
conn.close()

# ماركات معروفة حقيقية (علامات تجارية وليست أنواع منتجات)
known_brands = {
    # عصائر ومشروبات
    'المراعي', 'الربيع', 'جهينة', 'نانا', 'سن توب', 'كيمو', 'راني', 'ليبتون',
    'البساتين', 'المنتخب', 'تانج', 'تانجو', 'فيمتو', 'فوستر', 'بيبسي', 'كوكاكولا',
    'سفن اب', 'ميرندا', 'فانتا', 'سبرايت', 'ماونتن ديو', 'ريد بول', 'موكا',
    'لونا', 'هنيه', 'اورجنال', 'اورجنيال', 'كابري', 'مرحبا', 'بيريل', 'حياه',
    'اكوافينا', 'نوفا', 'هاسيا', 'بايسن', 'الصافي', 'مزون', 'السعودية', 'كي دي دي',
    'الهناء', 'الهنا', 'ريبون', 'لمار', 'اوسكار',
    
    # ألبان وأجبان
    'بوك', 'كيري', 'لافاشكيري', 'بيغا', 'بريزدنت', 'كرافت', 'ابو الولد',
    'المنارة', 'لونا', 'مذاقي', 'طابت',
    
    # بسكويت وشوكولاتة وحلويات
    'جولون', 'اوريو', 'اوليو', 'تيفاني', 'لوتس', 'بيماس', 'بريك تايم',
    'كيت كات', 'سنيكرز', 'مارس', 'تويكس', 'جالكسي', 'كادبوري', 'فيريرو',
    'كيندر', 'نوتيلا', 'باتشي', 'ديربي', 'الشمعدان', 'هاريبو', 'سكتلز',
    'ام اند امز', 'تروللي', 'مينتوس', 'ريجليز', 'كلوريتس', 'تيك تاك',
    'كراكر', 'ريتز', 'تاج', 'نيوتن', 'مكفيتيز', 'دانكن', 'بارنز',
    
    # شيبسات
    'نعمان', 'البطل', 'ليز', 'برنجلز', 'شيتوس', 'دوريتوس', 'تشي توس',
    
    # مواد غذائية
    'الدرة', 'حدائق', 'كاليفورنيا', 'ماجي', 'كنور', 'هاينز', 'قودي',
    'الامير', 'ارو', 'تاتا', 'روزانا', 'الوليمة', 'السعيد', 'العيد',
    'ابو كاس', 'ابو سيف',
    
    # سجائر ومعسل
    'مالبورو', 'ونستون', 'كاميل', 'كنت', 'دنهل', 'روثمان', 'بال مال',
    'الفاخر', 'نخلة', 'معسل',
    
    # منظفات
    'برسيل', 'اريال', 'تايد', 'داوني', 'فيري', 'بريل', 'كلوركس',
    'ديتول', 'فلاش', 'هاربيك', 'جف', 'فانيش', 'كومفرت', 'سيكا',
    'بونكس', 'مولوكاي', 'فين',
    
    # عناية شخصية
    'فاتيكا', 'دوف', 'كلير', 'هيد اند شولدرز', 'بانتين', 'صانسيلك',
    'لوكس', 'نيفيا', 'جونسون', 'هيمالايا', 'ويلز', 'لاكوست', 'بلاك',
    'جيليت', 'اولد سبايس', 'سيجنال', 'كولجيت', 'اورال بي', 'سنسوداين',
    'فازلين', 'بيوتي', 'بالمرز', 'غارنييه', 'لوريال',
    
    # أطفال
    'بامبرز', 'هجيز', 'برنس', 'جونسون', 'سيتافيل',
    'ميلوبا', 'سيميلاك', 'بيبيلاك', 'نان', 'ابتاميل',
    
    # زيوت
    'عافية', 'هيماني', 'فاتيكا', 'دابر',
    
    # أرز
    'ابو كاس', 'الوليمة', 'محسن', 'الشعلان',
    
    # آيسكريم
    'لندن', 'باسكن', 'كواليتي',
}

# كلمات عامة (أنواع منتجات وليست ماركات)
generic_words = {
    'بسكويت', 'شوكلاتة', 'شوكلاته', 'شامبو', 'صابون', 'عصير', 'حليب', 'شراب',
    'كريم', 'زيت', 'ارز', 'معجون', 'مسحوق', 'منظف', 'معطر', 'سائل',
    'مزيل', 'حلوى', 'ويفر', 'كيك', 'سجاره', 'سجائر', 'حفاظات',
    'سماعة', 'شاحن', 'علكه', 'طحينية', 'تونة', 'مكرونة', 'بطاطس',
    'فرشاة', 'ايسكريم', 'آيسكريم', 'مناديل', 'ماء', 'جبنة', 'جبن',
    'بودرة', 'معمول', 'صبغة', 'كف', 'ملعقة', 'شمع', 'شيشه',
    'هدايا', 'بخور', 'عطر', 'قهوة', 'شاي', 'سكر', 'ملح', 'خل',
    'فلفل', 'كمون', 'زنجبيل', 'دبس', 'عسل', 'منعم', 'لوشن',
    'بلاستيكية', 'كماشة', 'ولاعات', 'ولاعة', 'قفل', 'ميزان',
    'كيس', 'كأس', 'صحن', 'طبق', 'جوال', 'حقين', 'لبن', 'زبادي',
    'رول', 'ورق', 'شفرة', 'بطارية', 'لمبة', 'شريحة',
}

# تحليل كل صنف
detected = 0
not_detected = 0
brand_counts = {}
results_by_cat = {}

for p in products:
    name = p['name']
    words = name.split()
    found_brand = None
    
    # البحث في أول 3 كلمات
    for i in range(min(3, len(words))):
        # كلمة واحدة
        w = words[i]
        if w in known_brands:
            found_brand = w
            break
        # كلمتين
        if i + 1 < len(words):
            two = words[i] + ' ' + words[i+1]
            if two in known_brands:
                found_brand = two
                break
    
    # إذا الكلمة الأولى عامة، جرب الثانية
    if not found_brand and len(words) >= 2:
        if words[0].lower() in generic_words or words[0] in generic_words:
            if words[1] in known_brands:
                found_brand = words[1]
            elif len(words) >= 3:
                two = words[1] + ' ' + words[2]
                if two in known_brands:
                    found_brand = two
    
    cat = p['category_name'] or 'غير مصنف'
    if cat not in results_by_cat:
        results_by_cat[cat] = {'detected': 0, 'not_detected': 0, 'examples_detected': [], 'examples_not': []}
    
    if found_brand:
        detected += 1
        brand_counts[found_brand] = brand_counts.get(found_brand, 0) + 1
        results_by_cat[cat]['detected'] += 1
        if len(results_by_cat[cat]['examples_detected']) < 3:
            results_by_cat[cat]['examples_detected'].append((name[:50], found_brand))
    else:
        not_detected += 1
        results_by_cat[cat]['not_detected'] += 1
        if len(results_by_cat[cat]['examples_not']) < 3:
            results_by_cat[cat]['examples_not'].append(name[:50])

print("=" * 70)
print(f"نتائج التعرف على الماركات")
print("=" * 70)
print(f"إجمالي الأصناف: {len(products)}")
print(f"تم التعرف على ماركته: {detected} ({detected*100//len(products)}%)")
print(f"بدون ماركة معروفة: {not_detected} ({not_detected*100//len(products)}%)")
print(f"عدد الماركات المكتشفة: {len(brand_counts)}")

print(f"\n--- أكثر 30 ماركة ---")
for brand, cnt in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:30]:
    print(f"  {brand:<25} {cnt:>5} صنف")

print(f"\n--- حسب القسم ---")
for cat in sorted(results_by_cat.keys()):
    data = results_by_cat[cat]
    total_cat = data['detected'] + data['not_detected']
    pct = data['detected'] * 100 // total_cat if total_cat > 0 else 0
    print(f"\n  📂 {cat} ({total_cat} صنف) — {data['detected']} بماركة ({pct}%)")
    if data['examples_detected']:
        for name, brand in data['examples_detected']:
            print(f"     ✅ {name:<50} → {brand}")
    if data['examples_not'][:2]:
        for name in data['examples_not'][:2]:
            print(f"     ❌ {name}")
