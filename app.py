# -*- coding: utf-8 -*-
"""
🏪 نظام إدارة مشتريات السوبرماركت
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend: Flask + SQLite
Frontend: Tailwind CSS + Alpine.js
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash

# ═══════════════════════════════════════════════════════════════
# إعدادات التطبيق
# ═══════════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = 'supermarket-secret-key-2026'
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'supermarket.db')

# ═══════════════════════════════════════════════════════════════
# قاعدة البيانات
# ═══════════════════════════════════════════════════════════════

def get_db():
    """الحصول على اتصال قاعدة البيانات"""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(error):
    """إغلاق الاتصال"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """إنشاء جداول قاعدة البيانات"""
    db = get_db()
    
    # ─── المستخدمين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('manager', 'agent', 'warehouse')),
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ─── الموردين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            notes TEXT,
            balance REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ─── الأقسام ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    ''')
    
    # ─── الأصناف الداخلية (أسماؤك) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_en TEXT,
            receipt_name TEXT,
            barcode TEXT,
            category_id INTEGER,
            unit TEXT DEFAULT 'قطعة',
            min_stock REAL DEFAULT 0,
            current_stock REAL DEFAULT 0,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # ─── ربط أسماء المورد بأسمائك ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS supplier_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            supplier_product_name TEXT NOT NULL,
            supplier_product_code TEXT,
            product_id INTEGER NOT NULL,
            pack_size INTEGER DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE(supplier_id, supplier_product_name)
        )
    ''')
    
    # ─── إعدادات الفرز (صنف المورد يتفرز لأصناف محددة فقط) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS sorting_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_product_id INTEGER NOT NULL,
            allowed_product_id INTEGER NOT NULL,
            FOREIGN KEY (supplier_product_id) REFERENCES supplier_products(id) ON DELETE CASCADE,
            FOREIGN KEY (allowed_product_id) REFERENCES products(id),
            UNIQUE(supplier_product_id, allowed_product_id)
        )
    ''')
    
    # ─── أسعار الموردين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS supplier_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            pack_price REAL,
            pack_size INTEGER DEFAULT 1,
            effective_date TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # ─── المنافسين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # ─── أسعار المنافسين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS competitor_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            recorded_date TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (competitor_id) REFERENCES competitors(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # ─── تسعيرات البيع (عدة تسعيرات لكل صنف) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS price_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_default INTEGER DEFAULT 0
        )
    ''')
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS product_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price_list_id INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (price_list_id) REFERENCES price_lists(id),
            UNIQUE(product_id, price_list_id)
        )
    ''')
    
    # ─── فواتير المورد (لا تتعدل) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS supplier_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE,
            supplier_id INTEGER NOT NULL,
            invoice_date TEXT NOT NULL,
            total_amount REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'sorting', 'delivered', 'received')),
            notes TEXT,
            created_by INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # ─── بنود فاتورة المورد ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS supplier_invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            supplier_product_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            sorted_quantity REAL DEFAULT 0,
            FOREIGN KEY (invoice_id) REFERENCES supplier_invoices(id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_product_id) REFERENCES supplier_products(id)
        )
    ''')
    
    # ─── فاتورة المندوب (الفرز) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS agent_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_invoice_id INTEGER NOT NULL,
            agent_id INTEGER NOT NULL,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'submitted', 'received')),
            submitted_at TEXT,
            received_at TEXT,
            received_by INTEGER,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_invoice_id) REFERENCES supplier_invoices(id),
            FOREIGN KEY (agent_id) REFERENCES users(id),
            FOREIGN KEY (received_by) REFERENCES users(id)
        )
    ''')
    
    # ─── بنود فاتورة المندوب (التفريز) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS agent_invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_invoice_id INTEGER NOT NULL,
            supplier_invoice_item_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (agent_invoice_id) REFERENCES agent_invoices(id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_invoice_item_id) REFERENCES supplier_invoice_items(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # ─── حركات المخزون ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL CHECK(movement_type IN ('in', 'out', 'adjust')),
            quantity REAL NOT NULL,
            reference_type TEXT,
            reference_id INTEGER,
            notes TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # ─── إنشاء مستخدم افتراضي ───
    cursor = db.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        db.execute('''
            INSERT INTO users (username, password, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', generate_password_hash('admin'), 'مدير النظام', 'manager'))
    
    # ─── إنشاء قوائم أسعار افتراضية ───
    cursor = db.execute('SELECT COUNT(*) FROM price_lists')
    if cursor.fetchone()[0] == 0:
        db.execute("INSERT INTO price_lists (name, description, is_default) VALUES ('سعر المفرق', 'السعر العادي للعملاء', 1)")
        db.execute("INSERT INTO price_lists (name, description) VALUES ('سعر الجملة', 'سعر خاص للكميات الكبيرة')")
        db.execute("INSERT INTO price_lists (name, description) VALUES ('سعر خاص', 'سعر خاص لعملاء محددين')")
    
    db.commit()

# ═══════════════════════════════════════════════════════════════
# التحقق من تسجيل الدخول
# ═══════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'manager':
            flash('هذه الصفحة للمدير فقط', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ═══════════════════════════════════════════════════════════════
# الصفحات الرئيسية
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1',
            (username,)
        ).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f'مرحباً {user["full_name"]}', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('login'))

# ═══════════════════════════════════════════════════════════════
# إدارة المستخدمين
# ═══════════════════════════════════════════════════════════════

@app.route('/users')
@manager_required
def users():
    db = get_db()
    users_list = db.execute('''
        SELECT * FROM users ORDER BY role, full_name
    ''').fetchall()
    return render_template('users.html', users=users_list)

@app.route('/api/users', methods=['POST'])
@manager_required
def api_users_create():
    db = get_db()
    data = request.json
    
    # التحقق من عدم تكرار اسم المستخدم
    existing = db.execute('SELECT id FROM users WHERE username = ?', (data['username'],)).fetchone()
    if existing:
        return jsonify({'success': False, 'message': 'اسم المستخدم موجود مسبقاً'})
    
    db.execute('''
        INSERT INTO users (username, password, full_name, role)
        VALUES (?, ?, ?, ?)
    ''', (
        data['username'],
        generate_password_hash(data['password']),
        data['full_name'],
        data['role']
    ))
    db.commit()
    return jsonify({'success': True, 'message': 'تم إضافة المستخدم'})

@app.route('/api/users/<int:id>', methods=['PUT', 'DELETE'])
@manager_required
def api_user(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        
        # التحقق من عدم تكرار اسم المستخدم
        existing = db.execute('SELECT id FROM users WHERE username = ? AND id != ?', (data['username'], id)).fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'اسم المستخدم موجود مسبقاً'})
        
        db.execute('''
            UPDATE users SET username=?, full_name=?, role=?
            WHERE id=?
        ''', (data['username'], data['full_name'], data['role'], id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث المستخدم'})
    
    elif request.method == 'DELETE':
        # لا يمكن حذف المستخدم الحالي
        if id == session.get('user_id'):
            return jsonify({'success': False, 'message': 'لا يمكنك حذف نفسك'})
        
        db.execute('UPDATE users SET is_active=0 WHERE id=?', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تعطيل المستخدم'})

@app.route('/api/users/<int:id>/reset-password', methods=['POST'])
@manager_required
def api_user_reset_password(id):
    db = get_db()
    data = request.json
    
    db.execute('UPDATE users SET password=? WHERE id=?', 
               (generate_password_hash(data['password']), id))
    db.commit()
    return jsonify({'success': True, 'message': 'تم تغيير كلمة المرور'})

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        data = request.json
        db = get_db()
        
        # التحقق من كلمة المرور الحالية
        user = db.execute('SELECT password FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if not check_password_hash(user['password'], data['current_password']):
            return jsonify({'success': False, 'message': 'كلمة المرور الحالية غير صحيحة'})
        
        # تحديث كلمة المرور
        db.execute('UPDATE users SET password=? WHERE id=?',
                   (generate_password_hash(data['new_password']), session['user_id']))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تغيير كلمة المرور بنجاح'})
    
    return render_template('change_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    
    # إحصائيات سريعة
    stats = {
        'suppliers': db.execute('SELECT COUNT(*) FROM suppliers WHERE is_active=1').fetchone()[0],
        'products': db.execute('SELECT COUNT(*) FROM products WHERE is_active=1').fetchone()[0],
        'low_stock': db.execute('SELECT COUNT(*) FROM products WHERE current_stock <= min_stock AND is_active=1').fetchone()[0],
        'pending_invoices': db.execute("SELECT COUNT(*) FROM supplier_invoices WHERE status IN ('pending', 'sorting')").fetchone()[0],
        'pending_receive': db.execute("SELECT COUNT(*) FROM agent_invoices WHERE status = 'submitted'").fetchone()[0],
    }
    
    # آخر الفواتير
    recent_invoices = db.execute('''
        SELECT si.*, s.name as supplier_name, u.full_name as created_by_name
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        JOIN users u ON u.id = si.created_by
        ORDER BY si.created_at DESC LIMIT 5
    ''').fetchall()
    
    # أصناف تحت الحد الأدنى
    low_stock_items = db.execute('''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.current_stock <= p.min_stock AND p.is_active = 1
        ORDER BY (p.current_stock - p.min_stock) ASC
        LIMIT 10
    ''').fetchall()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_invoices=recent_invoices,
                         low_stock_items=low_stock_items)

# ═══════════════════════════════════════════════════════════════
# إدارة الموردين
# ═══════════════════════════════════════════════════════════════

@app.route('/suppliers')
@login_required
def suppliers():
    db = get_db()
    suppliers_list = db.execute('''
        SELECT s.*, 
               COUNT(DISTINCT sp.id) as products_count,
               COUNT(DISTINCT si.id) as invoices_count
        FROM suppliers s
        LEFT JOIN supplier_products sp ON sp.supplier_id = s.id
        LEFT JOIN supplier_invoices si ON si.supplier_id = s.id
        WHERE s.is_active = 1
        GROUP BY s.id
        ORDER BY s.name
    ''').fetchall()
    return render_template('suppliers.html', suppliers=suppliers_list)

@app.route('/api/suppliers', methods=['GET', 'POST'])
@login_required
def api_suppliers():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        db.execute('''
            INSERT INTO suppliers (name, phone, address, notes)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data.get('phone'), data.get('address'), data.get('notes')))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة المورد'})
    
    suppliers_list = db.execute('SELECT * FROM suppliers WHERE is_active=1 ORDER BY name').fetchall()
    return jsonify([dict(s) for s in suppliers_list])

@app.route('/api/suppliers/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_supplier(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        db.execute('''
            UPDATE suppliers SET name=?, phone=?, address=?, notes=?
            WHERE id=?
        ''', (data['name'], data.get('phone'), data.get('address'), data.get('notes'), id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث المورد'})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE suppliers SET is_active=0 WHERE id=?', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف المورد'})

# ═══════════════════════════════════════════════════════════════
# إدارة الأقسام
# ═══════════════════════════════════════════════════════════════

@app.route('/categories')
@login_required
def categories():
    db = get_db()
    categories_list = db.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM products WHERE category_id = c.id) as products_count,
               pc.name as parent_name
        FROM categories c
        LEFT JOIN categories pc ON pc.id = c.parent_id
        ORDER BY c.parent_id NULLS FIRST, c.sort_order, c.name
    ''').fetchall()
    return render_template('categories.html', categories=categories_list)

@app.route('/api/categories', methods=['GET', 'POST'])
@login_required
def api_categories():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        parent_id = data.get('parent_id')
        if parent_id == '' or parent_id == 0:
            parent_id = None
        db.execute('''
            INSERT INTO categories (name, parent_id, sort_order)
            VALUES (?, ?, ?)
        ''', (data['name'], parent_id, data.get('sort_order', 0)))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة القسم'})
    
    categories_list = db.execute('SELECT * FROM categories ORDER BY parent_id NULLS FIRST, sort_order, name').fetchall()
    return jsonify([dict(c) for c in categories_list])

@app.route('/api/categories/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_category(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        parent_id = data.get('parent_id')
        if parent_id == '' or parent_id == 0:
            parent_id = None
        db.execute('''
            UPDATE categories SET name=?, parent_id=?, sort_order=?
            WHERE id=?
        ''', (data['name'], parent_id, data.get('sort_order', 0), id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث القسم'})
    
    elif request.method == 'DELETE':
        # التحقق من وجود أصناف أو أقسام فرعية
        has_products = db.execute('SELECT COUNT(*) FROM products WHERE category_id = ?', (id,)).fetchone()[0]
        has_children = db.execute('SELECT COUNT(*) FROM categories WHERE parent_id = ?', (id,)).fetchone()[0]
        
        if has_products > 0:
            return jsonify({'success': False, 'message': f'لا يمكن حذف القسم - يحتوي على {has_products} صنف'})
        if has_children > 0:
            return jsonify({'success': False, 'message': f'لا يمكن حذف القسم - يحتوي على {has_children} قسم فرعي'})
        
        db.execute('DELETE FROM categories WHERE id=?', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف القسم'})

# ═══════════════════════════════════════════════════════════════
# إدارة الأصناف
# ═══════════════════════════════════════════════════════════════

@app.route('/products')
@login_required
def products():
    db = get_db()
    products_list = db.execute('''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.is_active = 1
        ORDER BY p.name
    ''').fetchall()
    categories = db.execute('SELECT * FROM categories ORDER BY name').fetchall()
    return render_template('products.html', products=products_list, categories=categories)

@app.route('/api/products', methods=['GET', 'POST'])
@login_required
def api_products():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        db.execute('''
            INSERT INTO products (name, name_en, receipt_name, barcode, category_id, unit, min_stock, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'], data.get('name_en'), data.get('receipt_name'),
            data.get('barcode'), data.get('category_id'), data.get('unit', 'قطعة'),
            data.get('min_stock', 0), data.get('notes')
        ))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة الصنف'})
    
    products_list = db.execute('''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.is_active = 1
        ORDER BY p.name
    ''').fetchall()
    return jsonify([dict(p) for p in products_list])

@app.route('/api/products/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_product(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        db.execute('''
            UPDATE products SET name=?, name_en=?, receipt_name=?, barcode=?,
                   category_id=?, unit=?, min_stock=?, notes=?
            WHERE id=?
        ''', (
            data['name'], data.get('name_en'), data.get('receipt_name'),
            data.get('barcode'), data.get('category_id'), data.get('unit'),
            data.get('min_stock', 0), data.get('notes'), id
        ))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث الصنف'})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE products SET is_active=0 WHERE id=?', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف الصنف'})

# ═══════════════════════════════════════════════════════════════
# ربط أسماء المورد + إعدادات الفرز
# ═══════════════════════════════════════════════════════════════

@app.route('/supplier-products')
@login_required
def supplier_products():
    db = get_db()
    supplier_id = request.args.get('supplier_id', type=int)
    
    query = '''
        SELECT sp.*, s.name as supplier_name, p.name as product_name,
               (SELECT COUNT(*) FROM sorting_rules WHERE supplier_product_id = sp.id) as sorting_count
        FROM supplier_products sp
        JOIN suppliers s ON s.id = sp.supplier_id
        JOIN products p ON p.id = sp.product_id
    '''
    if supplier_id:
        query += ' WHERE sp.supplier_id = ?'
        items = db.execute(query + ' ORDER BY sp.supplier_product_name', (supplier_id,)).fetchall()
    else:
        items = db.execute(query + ' ORDER BY s.name, sp.supplier_product_name').fetchall()
    
    suppliers = db.execute('SELECT * FROM suppliers WHERE is_active=1 ORDER BY name').fetchall()
    products_list = db.execute('SELECT * FROM products WHERE is_active=1 ORDER BY name').fetchall()
    
    return render_template('supplier_products.html', 
                         items=items, suppliers=suppliers, 
                         products=products_list, selected_supplier=supplier_id)

@app.route('/api/supplier-products', methods=['POST'])
@login_required
def api_supplier_products():
    db = get_db()
    data = request.json
    
    # الأصناف المسموح فرزها (أول صنف يكون الافتراضي)
    allowed_products = data.get('allowed_products', [])
    if not allowed_products:
        return jsonify({'success': False, 'message': 'يرجى اختيار صنف واحد على الأقل'})
    
    # أول صنف يكون الصنف الرئيسي المربوط
    primary_product_id = allowed_products[0]
    
    cursor = db.execute('''
        INSERT INTO supplier_products (supplier_id, supplier_product_name, supplier_product_code, product_id, pack_size, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['supplier_id'], data['supplier_product_name'], 
        data.get('supplier_product_code'), primary_product_id,
        data.get('pack_size', 1), data.get('notes')
    ))
    supplier_product_id = cursor.lastrowid
    
    # إضافة قواعد الفرز لكل الأصناف المسموحة
    for product_id in allowed_products:
        db.execute('''
            INSERT INTO sorting_rules (supplier_product_id, allowed_product_id)
            VALUES (?, ?)
        ''', (supplier_product_id, product_id))
    
    db.commit()
    
    return jsonify({'success': True, 'id': supplier_product_id, 'message': f'تم ربط الصنف مع {len(allowed_products)} أصناف للفرز'})

@app.route('/api/sorting-rules/<int:supplier_product_id>', methods=['GET', 'POST'])
@login_required
def api_sorting_rules(supplier_product_id):
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        # حذف القواعد القديمة
        db.execute('DELETE FROM sorting_rules WHERE supplier_product_id = ?', (supplier_product_id,))
        # إضافة الجديدة
        for product_id in data.get('allowed_products', []):
            db.execute('''
                INSERT INTO sorting_rules (supplier_product_id, allowed_product_id)
                VALUES (?, ?)
            ''', (supplier_product_id, product_id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حفظ إعدادات الفرز'})
    
    rules = db.execute('''
        SELECT sr.*, p.name as product_name
        FROM sorting_rules sr
        JOIN products p ON p.id = sr.allowed_product_id
        WHERE sr.supplier_product_id = ?
    ''', (supplier_product_id,)).fetchall()
    
    return jsonify([dict(r) for r in rules])

# ═══════════════════════════════════════════════════════════════
# أسعار الموردين + المقارنة
# ═══════════════════════════════════════════════════════════════

@app.route('/supplier-prices')
@login_required
def supplier_prices():
    db = get_db()
    
    # مقارنة أسعار الموردين لكل صنف
    comparison = db.execute('''
        SELECT p.id, p.name, p.unit,
               GROUP_CONCAT(s.name || ':' || sp.unit_price, '|') as prices
        FROM products p
        JOIN supplier_prices sp ON sp.product_id = p.id
        JOIN suppliers s ON s.id = sp.supplier_id
        WHERE p.is_active = 1
        GROUP BY p.id
        ORDER BY p.name
    ''').fetchall()
    
    suppliers = db.execute('SELECT * FROM suppliers WHERE is_active=1 ORDER BY name').fetchall()
    products_list = db.execute('SELECT * FROM products WHERE is_active=1 ORDER BY name').fetchall()
    
    return render_template('supplier_prices.html', 
                         comparison=comparison, 
                         suppliers=suppliers, 
                         products=products_list)

@app.route('/api/supplier-prices', methods=['POST'])
@login_required
def api_supplier_prices():
    db = get_db()
    data = request.json
    
    # تحديث أو إضافة السعر
    existing = db.execute('''
        SELECT id FROM supplier_prices 
        WHERE supplier_id = ? AND product_id = ?
    ''', (data['supplier_id'], data['product_id'])).fetchone()
    
    if existing:
        db.execute('''
            UPDATE supplier_prices SET unit_price=?, pack_price=?, pack_size=?, effective_date=?
            WHERE id=?
        ''', (data['unit_price'], data.get('pack_price'), data.get('pack_size', 1), 
              datetime.now().isoformat(), existing['id']))
    else:
        db.execute('''
            INSERT INTO supplier_prices (supplier_id, product_id, unit_price, pack_price, pack_size)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['supplier_id'], data['product_id'], data['unit_price'],
              data.get('pack_price'), data.get('pack_size', 1)))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم حفظ السعر'})

# ═══════════════════════════════════════════════════════════════
# أسعار المنافسين
# ═══════════════════════════════════════════════════════════════

@app.route('/competitor-prices')
@login_required
def competitor_prices():
    db = get_db()
    competitors = db.execute('SELECT * FROM competitors WHERE is_active=1 ORDER BY name').fetchall()
    products_list = db.execute('SELECT * FROM products WHERE is_active=1 ORDER BY name').fetchall()
    
    prices = db.execute('''
        SELECT cp.*, c.name as competitor_name, p.name as product_name
        FROM competitor_prices cp
        JOIN competitors c ON c.id = cp.competitor_id
        JOIN products p ON p.id = cp.product_id
        ORDER BY p.name, c.name
    ''').fetchall()
    
    return render_template('competitor_prices.html', 
                         competitors=competitors, 
                         products=products_list, 
                         prices=prices)

@app.route('/api/competitors', methods=['POST'])
@login_required
def api_competitors():
    db = get_db()
    data = request.json
    
    db.execute('''
        INSERT INTO competitors (name, address, notes)
        VALUES (?, ?, ?)
    ''', (data['name'], data.get('address'), data.get('notes')))
    db.commit()
    
    return jsonify({'success': True, 'message': 'تم إضافة المنافس'})

@app.route('/api/competitor-prices', methods=['POST'])
@login_required
def api_competitor_prices():
    db = get_db()
    data = request.json
    
    db.execute('''
        INSERT INTO competitor_prices (competitor_id, product_id, price)
        VALUES (?, ?, ?)
    ''', (data['competitor_id'], data['product_id'], data['price']))
    db.commit()
    
    return jsonify({'success': True, 'message': 'تم حفظ السعر'})

# ═══════════════════════════════════════════════════════════════
# تسعيرات البيع
# ═══════════════════════════════════════════════════════════════

@app.route('/pricing')
@login_required
def pricing():
    db = get_db()
    price_lists = db.execute('SELECT * FROM price_lists ORDER BY is_default DESC, name').fetchall()
    products_list = db.execute('SELECT * FROM products WHERE is_active=1 ORDER BY name').fetchall()
    
    # جلب كل الأسعار
    prices = db.execute('''
        SELECT pp.*, p.name as product_name, pl.name as price_list_name
        FROM product_prices pp
        JOIN products p ON p.id = pp.product_id
        JOIN price_lists pl ON pl.id = pp.price_list_id
        ORDER BY p.name, pl.is_default DESC
    ''').fetchall()
    
    return render_template('pricing.html', 
                         price_lists=price_lists, 
                         products=products_list, 
                         prices=prices)

@app.route('/api/product-prices', methods=['POST'])
@login_required
def api_product_prices():
    db = get_db()
    data = request.json
    
    # تحديث أو إضافة السعر
    existing = db.execute('''
        SELECT id FROM product_prices 
        WHERE product_id = ? AND price_list_id = ?
    ''', (data['product_id'], data['price_list_id'])).fetchone()
    
    if existing:
        db.execute('UPDATE product_prices SET price=? WHERE id=?',
                  (data['price'], existing['id']))
    else:
        db.execute('''
            INSERT INTO product_prices (product_id, price_list_id, price)
            VALUES (?, ?, ?)
        ''', (data['product_id'], data['price_list_id'], data['price']))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم حفظ السعر'})

# ═══════════════════════════════════════════════════════════════
# فواتير المورد
# ═══════════════════════════════════════════════════════════════

@app.route('/supplier-invoices')
@login_required
def supplier_invoices():
    db = get_db()
    
    invoices = db.execute('''
        SELECT si.*, s.name as supplier_name, u.full_name as created_by_name
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        JOIN users u ON u.id = si.created_by
        ORDER BY si.created_at DESC
    ''').fetchall()
    
    suppliers = db.execute('SELECT * FROM suppliers WHERE is_active=1 ORDER BY name').fetchall()
    
    return render_template('supplier_invoices.html', invoices=invoices, suppliers=suppliers)

@app.route('/supplier-invoices/<int:id>')
@login_required
def view_supplier_invoice(id):
    db = get_db()
    
    invoice = db.execute('''
        SELECT si.*, s.name as supplier_name, s.phone as supplier_phone,
               u.full_name as created_by_name
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        JOIN users u ON u.id = si.created_by
        WHERE si.id = ?
    ''', (id,)).fetchone()
    
    if not invoice:
        flash('الفاتورة غير موجودة', 'error')
        return redirect(url_for('supplier_invoices'))
    
    items = db.execute('''
        SELECT sii.*, sp.supplier_product_name, sp.pack_size, p.name as product_name
        FROM supplier_invoice_items sii
        JOIN supplier_products sp ON sp.id = sii.supplier_product_id
        JOIN products p ON p.id = sp.product_id
        WHERE sii.invoice_id = ?
    ''', (id,)).fetchall()
    
    return render_template('supplier_invoice_view.html', invoice=invoice, items=items)

@app.route('/api/supplier-invoices/<int:id>/pay', methods=['POST'])
@login_required
def pay_supplier_invoice(id):
    db = get_db()
    data = request.json
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'المبلغ غير صحيح'})
    
    db.execute('UPDATE supplier_invoices SET paid_amount = paid_amount + ? WHERE id = ?', (amount, id))
    db.commit()
    
    return jsonify({'success': True, 'message': f'تم تسجيل دفعة {amount:,.0f} ريال'})

@app.route('/supplier-invoices/new', methods=['GET', 'POST'])
@login_required
def new_supplier_invoice():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        
        # إنشاء رقم فاتورة تلقائي
        last = db.execute('SELECT MAX(id) FROM supplier_invoices').fetchone()[0] or 0
        invoice_number = f"SI-{datetime.now().strftime('%Y%m')}-{last+1:04d}"
        
        cursor = db.execute('''
            INSERT INTO supplier_invoices (invoice_number, supplier_id, invoice_date, total_amount, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            invoice_number, data['supplier_id'], data['invoice_date'],
            data['total_amount'], data.get('notes'), session['user_id']
        ))
        invoice_id = cursor.lastrowid
        
        # إضافة البنود
        for item in data['items']:
            db.execute('''
                INSERT INTO supplier_invoice_items (invoice_id, supplier_product_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (invoice_id, item['supplier_product_id'], item['quantity'], 
                  item['unit_price'], item['total_price']))
        
        db.commit()
        return jsonify({'success': True, 'id': invoice_id, 'invoice_number': invoice_number})
    
    suppliers = db.execute('SELECT * FROM suppliers WHERE is_active=1 ORDER BY name').fetchall()
    return render_template('supplier_invoice_form.html', suppliers=suppliers)

@app.route('/api/supplier/<int:supplier_id>/products')
@login_required
def api_supplier_product_list(supplier_id):
    db = get_db()
    items = db.execute('''
        SELECT sp.*, p.name as product_name
        FROM supplier_products sp
        JOIN products p ON p.id = sp.product_id
        WHERE sp.supplier_id = ?
        ORDER BY sp.supplier_product_name
    ''', (supplier_id,)).fetchall()
    return jsonify([dict(i) for i in items])

# ═══════════════════════════════════════════════════════════════
# فاتورة المندوب (الفرز)
# ═══════════════════════════════════════════════════════════════

@app.route('/agent-invoices')
@login_required
def agent_invoices():
    db = get_db()
    
    invoices = db.execute('''
        SELECT ai.*, si.invoice_number, s.name as supplier_name, 
               u.full_name as agent_name, ur.full_name as received_by_name
        FROM agent_invoices ai
        JOIN supplier_invoices si ON si.id = ai.supplier_invoice_id
        JOIN suppliers s ON s.id = si.supplier_id
        JOIN users u ON u.id = ai.agent_id
        LEFT JOIN users ur ON ur.id = ai.received_by
        ORDER BY ai.created_at DESC
    ''').fetchall()
    
    # فواتير بانتظار الفرز
    pending = db.execute('''
        SELECT si.*, s.name as supplier_name
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        WHERE si.status = 'pending'
        ORDER BY si.created_at
    ''').fetchall()
    
    return render_template('agent_invoices.html', invoices=invoices, pending=pending)

@app.route('/agent-invoices/<int:supplier_invoice_id>/sort', methods=['GET', 'POST'])
@login_required
def sort_invoice(supplier_invoice_id):
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        
        # إنشاء فاتورة المندوب
        cursor = db.execute('''
            INSERT INTO agent_invoices (supplier_invoice_id, agent_id, status)
            VALUES (?, ?, 'draft')
        ''', (supplier_invoice_id, session['user_id']))
        agent_invoice_id = cursor.lastrowid
        
        # إضافة بنود الفرز
        for item in data['items']:
            db.execute('''
                INSERT INTO agent_invoice_items (agent_invoice_id, supplier_invoice_item_id, product_id, quantity)
                VALUES (?, ?, ?, ?)
            ''', (agent_invoice_id, item['supplier_invoice_item_id'], 
                  item['product_id'], item['quantity']))
            
            # تحديث الكمية المفرزة في فاتورة المورد
            db.execute('''
                UPDATE supplier_invoice_items 
                SET sorted_quantity = sorted_quantity + ?
                WHERE id = ?
            ''', (item['quantity'], item['supplier_invoice_item_id']))
        
        # تحديث حالة فاتورة المورد
        db.execute("UPDATE supplier_invoices SET status = 'sorting' WHERE id = ?", (supplier_invoice_id,))
        
        db.commit()
        return jsonify({'success': True, 'id': agent_invoice_id})
    
    # جلب بيانات فاتورة المورد
    invoice = db.execute('''
        SELECT si.*, s.name as supplier_name
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        WHERE si.id = ?
    ''', (supplier_invoice_id,)).fetchone()
    
    items = db.execute('''
        SELECT sii.*, sp.supplier_product_name, sp.pack_size, p.name as product_name
        FROM supplier_invoice_items sii
        JOIN supplier_products sp ON sp.id = sii.supplier_product_id
        JOIN products p ON p.id = sp.product_id
        WHERE sii.invoice_id = ?
    ''', (supplier_invoice_id,)).fetchall()
    
    # جلب قواعد الفرز لكل صنف
    items_with_rules = []
    for item in items:
        rules = db.execute('''
            SELECT sr.allowed_product_id, p.name as product_name
            FROM sorting_rules sr
            JOIN products p ON p.id = sr.allowed_product_id
            WHERE sr.supplier_product_id = ?
        ''', (item['supplier_product_id'],)).fetchall()
        
        items_with_rules.append({
            **dict(item),
            'allowed_products': [dict(r) for r in rules]
        })
    
    return render_template('sort_invoice.html', invoice=invoice, items=items_with_rules)

@app.route('/api/agent-invoices/<int:id>/submit', methods=['POST'])
@login_required
def submit_agent_invoice(id):
    db = get_db()
    db.execute('''
        UPDATE agent_invoices SET status = 'submitted', submitted_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), id))
    
    # تحديث حالة فاتورة المورد
    invoice = db.execute('SELECT supplier_invoice_id FROM agent_invoices WHERE id = ?', (id,)).fetchone()
    db.execute("UPDATE supplier_invoices SET status = 'delivered' WHERE id = ?", (invoice['supplier_invoice_id'],))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم تسليم الفاتورة للمخزن'})

# ═══════════════════════════════════════════════════════════════
# استلام المخزن
# ═══════════════════════════════════════════════════════════════

@app.route('/warehouse')
@login_required
def warehouse():
    db = get_db()
    
    # فواتير بانتظار الاستلام
    pending = db.execute('''
        SELECT ai.*, si.invoice_number, s.name as supplier_name, u.full_name as agent_name
        FROM agent_invoices ai
        JOIN supplier_invoices si ON si.id = ai.supplier_invoice_id
        JOIN suppliers s ON s.id = si.supplier_id
        JOIN users u ON u.id = ai.agent_id
        WHERE ai.status = 'submitted'
        ORDER BY ai.submitted_at
    ''').fetchall()
    
    # آخر الاستلامات
    recent = db.execute('''
        SELECT ai.*, si.invoice_number, s.name as supplier_name, 
               u.full_name as agent_name, ur.full_name as received_by_name
        FROM agent_invoices ai
        JOIN supplier_invoices si ON si.id = ai.supplier_invoice_id
        JOIN suppliers s ON s.id = si.supplier_id
        JOIN users u ON u.id = ai.agent_id
        JOIN users ur ON ur.id = ai.received_by
        WHERE ai.status = 'received'
        ORDER BY ai.received_at DESC
        LIMIT 10
    ''').fetchall()
    
    return render_template('warehouse.html', pending=pending, recent=recent)

@app.route('/api/warehouse/receive/<int:agent_invoice_id>', methods=['POST'])
@login_required
def receive_invoice(agent_invoice_id):
    db = get_db()
    
    # تحديث حالة فاتورة المندوب
    db.execute('''
        UPDATE agent_invoices 
        SET status = 'received', received_at = ?, received_by = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), session['user_id'], agent_invoice_id))
    
    # جلب البنود وتحديث المخزون
    items = db.execute('''
        SELECT aii.product_id, aii.quantity
        FROM agent_invoice_items aii
        WHERE aii.agent_invoice_id = ?
    ''', (agent_invoice_id,)).fetchall()
    
    for item in items:
        # تحديث المخزون
        db.execute('''
            UPDATE products SET current_stock = current_stock + ?
            WHERE id = ?
        ''', (item['quantity'], item['product_id']))
        
        # تسجيل حركة المخزون
        db.execute('''
            INSERT INTO inventory_movements (product_id, movement_type, quantity, reference_type, reference_id, created_by)
            VALUES (?, 'in', ?, 'agent_invoice', ?, ?)
        ''', (item['product_id'], item['quantity'], agent_invoice_id, session['user_id']))
    
    # تحديث حالة فاتورة المورد
    invoice = db.execute('SELECT supplier_invoice_id FROM agent_invoices WHERE id = ?', (agent_invoice_id,)).fetchone()
    db.execute("UPDATE supplier_invoices SET status = 'received' WHERE id = ?", (invoice['supplier_invoice_id'],))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم استلام البضاعة وتحديث المخزون'})

# ═══════════════════════════════════════════════════════════════
# المخزون
# ═══════════════════════════════════════════════════════════════

@app.route('/inventory')
@login_required
def inventory():
    db = get_db()
    
    products_list = db.execute('''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.is_active = 1
        ORDER BY p.name
    ''').fetchall()
    
    # حساب الإحصائيات
    stats = {
        'total': len(products_list),
        'above_min': sum(1 for p in products_list if p['current_stock'] > p['min_stock']),
        'below_min': sum(1 for p in products_list if p['current_stock'] <= p['min_stock'] and p['current_stock'] > 0),
        'zero_stock': sum(1 for p in products_list if p['current_stock'] == 0),
    }
    
    return render_template('inventory.html', products=products_list, stats=stats)

@app.route('/api/inventory/movements/<int:product_id>')
@login_required
def product_movements(product_id):
    db = get_db()
    movements = db.execute('''
        SELECT im.*, u.full_name as created_by_name
        FROM inventory_movements im
        LEFT JOIN users u ON u.id = im.created_by
        WHERE im.product_id = ?
        ORDER BY im.created_at DESC
        LIMIT 50
    ''', (product_id,)).fetchall()
    return jsonify([dict(m) for m in movements])

# ═══════════════════════════════════════════════════════════════
# التقارير
# ═══════════════════════════════════════════════════════════════

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/api/reports/purchases')
@login_required
def report_purchases():
    db = get_db()
    start = request.args.get('start', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end = request.args.get('end', datetime.now().strftime('%Y-%m-%d'))
    
    data = db.execute('''
        SELECT s.name as supplier_name, SUM(si.total_amount) as total,
               COUNT(si.id) as invoice_count
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        WHERE si.invoice_date BETWEEN ? AND ?
        GROUP BY s.id
        ORDER BY total DESC
    ''', (start, end)).fetchall()
    
    return jsonify([dict(d) for d in data])

@app.route('/api/reports/supplier-debts')
@login_required
def report_supplier_debts():
    db = get_db()
    data = db.execute('''
        SELECT s.name, s.balance,
               SUM(si.total_amount) as total_invoices,
               SUM(si.paid_amount) as total_paid
        FROM suppliers s
        LEFT JOIN supplier_invoices si ON si.supplier_id = s.id
        WHERE s.is_active = 1
        GROUP BY s.id
        HAVING (SUM(si.total_amount) - SUM(si.paid_amount)) > 0
        ORDER BY (SUM(si.total_amount) - SUM(si.paid_amount)) DESC
    ''').fetchall()
    return jsonify([dict(d) for d in data])

# ═══════════════════════════════════════════════════════════════
# تشغيل التطبيق
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    print('=' * 50)
    print('Supermarket Management System')
    print('=' * 50)
    print('URL: http://localhost:5000')
    print('User: admin')
    print('Password: admin')
    print('=' * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False, threaded=True)
