import sqlite3

def migrate():
    conn = sqlite3.connect('supermarket.db')
    cursor = conn.cursor()
    
    # إضافة أعمدة الموقع للموردين
    columns_to_add = [
        ('latitude', 'REAL'),
        ('longitude', 'REAL'),
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE suppliers ADD COLUMN {column_name} {column_type}')
            print(f'✅ تمت إضافة عمود {column_name}')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f'⚠️ العمود {column_name} موجود مسبقاً')
            else:
                print(f'❌ خطأ: {e}')
    
    conn.commit()
    conn.close()
    print('✅ تم تحديث قاعدة البيانات بنجاح')

if __name__ == '__main__':
    migrate()
