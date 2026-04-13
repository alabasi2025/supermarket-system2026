# -*- coding: utf-8 -*-
"""
🏪 نظام إدارة مشتريات السوبرماركت
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend: Flask + PostgreSQL
Frontend: Tailwind CSS + Alpine.js
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import secrets
import psycopg2
import psycopg2.extras
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
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(32)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # No cache during development

# PostgreSQL Configuration
app.config['PG_HOST'] = os.environ.get('PG_HOST', 'localhost')
app.config['PG_PORT'] = os.environ.get('PG_PORT', '5432')
app.config['PG_DATABASE'] = os.environ.get('PG_DATABASE', 'supermarket')
app.config['PG_USER'] = os.environ.get('PG_USER', 'postgres')
app.config['PG_PASSWORD'] = os.environ.get('PG_PASSWORD', '774424555')

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', '0') == '1'

# ═══════════════════════════════════════════════════════════════
# قاعدة البيانات PostgreSQL
# ═══════════════════════════════════════════════════════════════

class PostgreSQLWrapper:
    """Wrapper to make PostgreSQL work like SQLite's db.execute() pattern"""
    
    def __init__(self, conn):
        self.conn = conn
        self._cursor = None
    
    def execute(self, query, params=None):
        """Execute a query and return cursor-like object"""
        self._cursor = self.conn.cursor()
        if params:
            self._cursor.execute(query, params)
        else:
            self._cursor.execute(query)
        return CursorWrapper(self._cursor, self.conn)
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()
    
    def close(self):
        self.conn.close()
    
    @property
    def lastrowid(self):
        return self._cursor.fetchone()['id'] if self._cursor else None

class CursorWrapper:
    """Wrapper for cursor to support fetchone/fetchall with dict-like access"""
    
    def __init__(self, cursor, conn):
        self.cursor = cursor
        self.conn = conn
        self._lastrowid = None
    
    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    
    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    @property
    def lastrowid(self):
        return self._lastrowid
    
    @property
    def rowcount(self):
        return self.cursor.rowcount

def get_db():
    """الحصول على اتصال قاعدة البيانات PostgreSQL"""
    if 'db' not in g:
        conn = psycopg2.connect(
            host=app.config['PG_HOST'],
            port=app.config['PG_PORT'],
            database=app.config['PG_DATABASE'],
            user=app.config['PG_USER'],
            password=app.config['PG_PASSWORD'],
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        g.db = PostgreSQLWrapper(conn)
    return g.db

def get_cursor():
    """الحصول على cursor"""
    db = get_db()
    return db.conn.cursor()

@app.teardown_appcontext
def close_db(error):
    """إغلاق الاتصال"""
    db = g.pop('db', None)
    if db is not None:
        if error is None:
            db.commit()
        db.close()

def table_exists(db, table_name):
    """التحقق من وجود جدول في قاعدة البيانات"""
    result = db.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        ) as exists
    """, (table_name,))
    return result.fetchone()['exists']

def init_db():
    """إنشاء جداول قاعدة البيانات"""
    db = get_db()
    
    # ─── المستخدمين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY ,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('manager', 'agent', 'warehouse')),
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ─── الموظفين (مع مواقع السكن) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY ,
            user_id INTEGER,
            name TEXT NOT NULL,
            job_title TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            department TEXT,
            hire_date TEXT,
            salary REAL,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ─── الموردين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            notes TEXT,
            balance REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ─── أرقام جوال المورد ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS supplier_phones (
            id SERIAL PRIMARY KEY ,
            supplier_id INTEGER NOT NULL,
            phone TEXT NOT NULL,
            label TEXT DEFAULT 'جوال',
            is_primary INTEGER DEFAULT 0,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
        )
    ''')

    # ─── حساباتك المسجلة عند المورد ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS supplier_accounts (
            id SERIAL PRIMARY KEY ,
            supplier_id INTEGER NOT NULL,
            account_name TEXT NOT NULL,
            account_number TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
        )
    ''')

    # ─── المنافسين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS competitors (
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'سوبرماركت',
            phone TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ─── المخازن ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS warehouses (
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL,
            manager_id INTEGER,
            capacity TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES employees(id)
        )
    ''')
    
    # ─── الفروع/المتاجر ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS stores (
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            latitude REAL,
            longitude REAL,
            manager_id INTEGER,
            working_hours TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES employees(id)
        )
    ''')
    
    # ─── الإشعارات ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY ,
            user_id INTEGER,
            title TEXT NOT NULL,
            message TEXT,
            type TEXT DEFAULT 'info' CHECK(type IN ('info', 'warning', 'error', 'success')),
            is_read INTEGER DEFAULT 0,
            link TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ─── سجل التدقيق ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY ,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_data TEXT,
            new_data TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ─── الوحدات ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL UNIQUE,
            symbol TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # ─── الأقسام ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL,
            parent_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    ''')
    
    # ─── الأصناف الداخلية (أسماؤك) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL,
            name_en TEXT,
            receipt_name TEXT,
            barcode TEXT,
            product_code TEXT,
            brand TEXT,
            category_id INTEGER,
            unit TEXT DEFAULT 'قطعة',
            pack_size INTEGER DEFAULT 1,
            cost_price REAL DEFAULT 0,
            sell_price REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            current_stock REAL DEFAULT 0,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # ─── وحدات الصنف المتعددة ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS product_units (
            id SERIAL PRIMARY KEY ,
            product_id INTEGER NOT NULL,
            unit_id INTEGER NOT NULL,
            conversion_factor REAL DEFAULT 1,
            barcode TEXT,
            price REAL DEFAULT 0,
            is_default INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (unit_id) REFERENCES units(id),
            UNIQUE(product_id, unit_id)
        )
    ''')
    
    # ─── ربط أسماء المورد بأسمائك ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS supplier_products (
            id SERIAL PRIMARY KEY ,
            supplier_id INTEGER NOT NULL,
            supplier_product_name TEXT NOT NULL,
            supplier_product_code TEXT,
            supplier_barcode TEXT,
            supplier_unit TEXT DEFAULT 'كرتون',
            product_id INTEGER,
            pack_size INTEGER DEFAULT 1,
            purchase_price REAL DEFAULT 0,
            min_order_qty INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE(supplier_id, supplier_product_name)
        )
    ''')
    # migration: جعل product_id اختيارياً في قواعد البيانات القديمة
    try:
        cols = [r[1] for r in db.execute('PRAGMA table_info(supplier_products)').fetchall()]
        if 'product_id' in cols:
            db.execute('''
                CREATE TABLE IF NOT EXISTS supplier_products_new (
                    id SERIAL PRIMARY KEY ,
                    supplier_id INTEGER NOT NULL,
                    supplier_product_name TEXT NOT NULL,
                    supplier_product_code TEXT,
                    supplier_barcode TEXT,
                    supplier_unit TEXT DEFAULT 'كرتون',
                    product_id INTEGER,
                    pack_size INTEGER DEFAULT 1,
                    purchase_price REAL DEFAULT 0,
                    min_order_qty INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    notes TEXT,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    UNIQUE(supplier_id, supplier_product_name)
                )
            ''')
            existing = db.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="supplier_products_new"').fetchone()
            if existing:
                db.execute('INSERT OR IGNORE INTO supplier_products_new SELECT * FROM supplier_products')
                db.execute('DROP TABLE supplier_products')
                db.execute('ALTER TABLE supplier_products_new RENAME TO supplier_products')
                db.commit()
    except Exception:
        pass
    
    # ─── إعدادات الفرز (صنف المورد يتفرز لأصناف محددة فقط) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS sorting_rules (
            id SERIAL PRIMARY KEY ,
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
            id SERIAL PRIMARY KEY ,
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
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL,
            address TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # ─── أسعار المنافسين ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS competitor_prices (
            id SERIAL PRIMARY KEY ,
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
            id SERIAL PRIMARY KEY ,
            name TEXT NOT NULL,
            description TEXT,
            is_default INTEGER DEFAULT 0
        )
    ''')
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS product_prices (
            id SERIAL PRIMARY KEY ,
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
            id SERIAL PRIMARY KEY ,
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
            id SERIAL PRIMARY KEY ,
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
            id SERIAL PRIMARY KEY ,
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
            id SERIAL PRIMARY KEY ,
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
            id SERIAL PRIMARY KEY ,
            product_id INTEGER NOT NULL,
            batch_id INTEGER,
            movement_type TEXT NOT NULL CHECK(movement_type IN ('in', 'out', 'adjust')),
            quantity REAL NOT NULL,
            reference_type TEXT,
            reference_id INTEGER,
            notes TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (batch_id) REFERENCES product_batches(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # ─── دفعات المنتجات (تتبع تواريخ الإنتاج والانتهاء) ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS product_batches (
            id SERIAL PRIMARY KEY ,
            product_id INTEGER NOT NULL,
            batch_number TEXT,
            production_date TEXT,
            expiry_date TEXT,
            quantity_received REAL NOT NULL DEFAULT 0,
            quantity_remaining REAL NOT NULL DEFAULT 0,
            purchase_price REAL,
            supplier_invoice_id INTEGER,
            supplier_invoice_item_id INTEGER,
            location TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'expired', 'consumed', 'returned')),
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (supplier_invoice_id) REFERENCES supplier_invoices(id),
            FOREIGN KEY (supplier_invoice_item_id) REFERENCES supplier_invoice_items(id)
        )
    ''')
    
    # ─── تنبيهات انتهاء الصلاحية ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS expiry_alerts (
            id SERIAL PRIMARY KEY ,
            batch_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL CHECK(alert_type IN ('approaching', 'expired', 'low_stock')),
            alert_date TEXT NOT NULL,
            is_handled INTEGER DEFAULT 0,
            handled_by INTEGER,
            handled_at TEXT,
            action_taken TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES product_batches(id),
            FOREIGN KEY (handled_by) REFERENCES users(id)
        )
    ''')
    
    # ─── فواتير نقاط البيع ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS pos_invoices (
            id SERIAL PRIMARY KEY ,
            invoice_number TEXT UNIQUE NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash' CHECK(payment_method IN ('cash', 'card', 'bank', 'credit', 'mixed')),
            paid_amount REAL DEFAULT 0,
            change_amount REAL DEFAULT 0,
            customer_name TEXT,
            customer_phone TEXT,
            customer_id INTEGER,
            shift_id INTEGER,
            notes TEXT,
            status TEXT DEFAULT 'completed' CHECK(status IN ('completed', 'cancelled', 'refunded')),
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # ─── بنود فواتير نقاط البيع ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS pos_invoice_items (
            id SERIAL PRIMARY KEY ,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,
            discount REAL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            batch_id INTEGER,
            FOREIGN KEY (invoice_id) REFERENCES pos_invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (batch_id) REFERENCES product_batches(id)
        )
    ''')
    
    # ─── ورديات الكاشير ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS pos_shifts (
            id SERIAL PRIMARY KEY ,
            user_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            opening_balance REAL DEFAULT 0,
            closing_balance REAL,
            total_cash REAL DEFAULT 0,
            total_card REAL DEFAULT 0,
            total_sales REAL DEFAULT 0,
            total_refunds REAL DEFAULT 0,
            status TEXT DEFAULT 'open' CHECK(status IN ('open', 'closed')),
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ─── مرتجعات نقاط البيع ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS pos_returns (
            id SERIAL PRIMARY KEY ,
            return_number TEXT UNIQUE NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0,
            refund_method TEXT DEFAULT 'cash' CHECK(refund_method IN ('cash', 'credit')),
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # ─── بنود المرتجعات ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS pos_return_items (
            id SERIAL PRIMARY KEY ,
            return_id INTEGER NOT NULL,
            invoice_id INTEGER,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,
            reason TEXT,
            FOREIGN KEY (return_id) REFERENCES pos_returns(id),
            FOREIGN KEY (invoice_id) REFERENCES pos_invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # ─── إعدادات النظام ───
    db.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT
        )
    ''')
    
    # ─── إنشاء مستخدم افتراضي ───
    cursor = db.execute('SELECT COUNT(*) as count FROM users')
    if cursor.fetchone()['count'] == 0:
        db.execute('''
            INSERT INTO users (username, password, full_name, role)
            VALUES (%s, %s, %s, %s)
        ''', ('admin', generate_password_hash('admin'), 'مدير النظام', 'manager'))
    
    # ─── إعدادات افتراضية ───
    default_settings = [
        ('store_name', 'سوبرماركت', 'اسم المتجر'),
        ('store_phone', '', 'رقم الهاتف'),
        ('store_address', '', 'العنوان'),
        ('currency', 'ريال', 'العملة'),
        ('tax_rate', '0', 'نسبة الضريبة %'),
    ]
    for key, value, desc in default_settings:
        db.execute('INSERT OR IGNORE INTO settings (key, value, description) VALUES (%s, %s, %s)', (key, value, desc))
    
    # ─── إنشاء قوائم أسعار افتراضية ───
    cursor = db.execute('SELECT COUNT(*) as count FROM price_lists')
    if cursor.fetchone()['count'] == 0:
        db.execute("INSERT INTO price_lists (name, description, is_default) VALUES ('سعر المفرق', 'السعر العادي للعملاء', 1)")
        db.execute("INSERT INTO price_lists (name, description) VALUES ('سعر الجملة', 'سعر خاص للكميات الكبيرة')")
        db.execute("INSERT INTO price_lists (name, description) VALUES ('سعر خاص', 'سعر خاص لعملاء محددين')")
    
    # ─── إنشاء وحدات افتراضية ───
    cursor = db.execute('SELECT COUNT(*) as count FROM units')
    if cursor.fetchone()['count'] == 0:
        default_units = [
            ('قطعة', 'قطعة'),
            ('كرتون', 'كرتون'),
            ('كيلو', 'كجم'),
            ('جرام', 'جم'),
            ('لتر', 'لتر'),
            ('مل', 'مل'),
            ('باكت', 'باكت'),
            ('علبة', 'علبة'),
            ('كيس', 'كيس'),
            ('شدة', 'شدة'),
            ('صندوق', 'صندوق'),
            ('شوال', 'شوال'),
            ('درزن', 'درزن'),
            ('متر', 'م'),
        ]
        for unit_name, symbol in default_units:
            db.execute("INSERT INTO units (name, symbol) VALUES (%s, %s)", (unit_name, symbol))
    
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
        if session.get('must_change_password'):
            return redirect(url_for('force_change_password'))
        return f(*args, **kwargs)
    return decorated_function

def is_api_request():
    return request.path.startswith('/api/') or request.is_json

def forbidden_response(message):
    if is_api_request():
        return jsonify({'success': False, 'message': message}), 403
    flash(message, 'error')
    return redirect(url_for('dashboard'))

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('must_change_password'):
            return redirect(url_for('force_change_password'))
        if session.get('role') != 'manager':
            return forbidden_response('هذه الصفحة للمدير فقط')
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            if session.get('must_change_password'):
                return redirect(url_for('force_change_password'))

            if session.get('role') not in allowed_roles:
                return forbidden_response('ليس لديك صلاحية للوصول إلى هذه الصفحة')

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token

@app.context_processor
def inject_csrf_token():
    return {'csrf_token': get_csrf_token}

@app.before_request
def csrf_protect():
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return None
    
    # استثناء بعض الصفحات من CSRF
    csrf_exempt = ['/api/pos/verify-pin', '/api/pos/invoice', '/api/pos/return', '/force-change-password']
    if any(request.path.startswith(path) for path in csrf_exempt):
        return None

    session_token = session.get('_csrf_token')
    request_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')

    if session_token and request_token and secrets.compare_digest(session_token, request_token):
        return None

    if is_api_request():
        return jsonify({'success': False, 'message': 'رمز الحماية غير صالح، أعد تحميل الصفحة وحاول مرة أخرى'}), 400

    flash('الطلب غير صالح، أعد تحميل الصفحة وحاول مرة أخرى', 'error')
    return redirect(url_for('login'))

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
            'SELECT * FROM users WHERE username = %s AND is_active = 1',
            (username,)
        ).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            get_csrf_token()
            
            # Check if must change password
            if user['must_change_password']:
                session['must_change_password'] = True
                return redirect(url_for('force_change_password'))
            
            flash(f'مرحباً {user["full_name"]}', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/force-change-password', methods=['GET', 'POST'])
def force_change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if len(new_password) < 4:
            flash('كلمة المرور يجب أن تكون 4 أحرف على الأقل', 'error')
        elif new_password != confirm_password:
            flash('كلمة المرور غير متطابقة', 'error')
        else:
            db = get_db()
            user_id = session['user_id']
            db.execute('UPDATE users SET password=%s, must_change_password=0 WHERE id=%s',
                      (generate_password_hash(new_password), user_id))
            db.commit()
            
            # تحديث الجلسة
            session.pop('must_change_password', None)
            session.modified = True
            
            flash('تم تغيير كلمة المرور بنجاح', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('force_change_password.html')

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
    existing = db.execute('SELECT id FROM users WHERE username = %s', (data['username'],)).fetchone()
    if existing:
        return jsonify({'success': False, 'message': 'اسم المستخدم موجود مسبقاً'})
    
    db.execute('''
        INSERT INTO users (username, password, full_name, role)
        VALUES (%s, %s, %s, %s)
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
        existing = db.execute('SELECT id FROM users WHERE username = %s AND id != %s', (data['username'], id)).fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'اسم المستخدم موجود مسبقاً'})
        
        db.execute('''
            UPDATE users SET username=%s, full_name=%s, role=%s
            WHERE id=%s
        ''', (data['username'], data['full_name'], data['role'], id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث المستخدم'})
    
    elif request.method == 'DELETE':
        # لا يمكن حذف المستخدم الحالي
        if id == session.get('user_id'):
            return jsonify({'success': False, 'message': 'لا يمكنك حذف نفسك'})
        
        db.execute('UPDATE users SET is_active=0 WHERE id=%s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تعطيل المستخدم'})

@app.route('/api/users/<int:id>/reset-password', methods=['POST'])
@manager_required
def api_user_reset_password(id):
    db = get_db()
    data = request.json
    
    db.execute('UPDATE users SET password=%s WHERE id=%s', 
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
        user = db.execute('SELECT password FROM users WHERE id = %s', (session['user_id'],)).fetchone()
        if not check_password_hash(user['password'], data['current_password']):
            return jsonify({'success': False, 'message': 'كلمة المرور الحالية غير صحيحة'})
        
        # تحديث كلمة المرور
        db.execute('UPDATE users SET password=%s WHERE id=%s',
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
        'suppliers': db.execute('SELECT COUNT(*) as count FROM suppliers WHERE is_active=1').fetchone()['count'],
        'products': db.execute('SELECT COUNT(*) as count FROM products WHERE is_active=1').fetchone()['count'],
        'low_stock': db.execute('SELECT COUNT(*) as count FROM products WHERE current_stock <= min_stock AND is_active=1').fetchone()['count'],
        'pending_invoices': db.execute("SELECT COUNT(*) as count FROM supplier_invoices WHERE status IN ('pending', 'sorting')").fetchone()['count'],
        'pending_receive': db.execute("SELECT COUNT(*) as count FROM agent_invoices WHERE status = 'submitted'").fetchone()['count'],
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
@role_required('manager')
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

@app.route('/maps')
@role_required('manager')
def maps():
    db = get_db()
    # الموردين
    suppliers_list = db.execute('''
        SELECT * FROM suppliers WHERE is_active = 1 ORDER BY name
    ''').fetchall()
    
    # المنافسين
    competitors_list = db.execute('''
        SELECT * FROM competitors WHERE is_active = 1 ORDER BY name
    ''').fetchall() if table_exists(db, 'competitors') else []
    
    # المخازن
    warehouses_list = db.execute('''
        SELECT * FROM warehouses WHERE is_active = 1 ORDER BY name
    ''').fetchall() if table_exists(db, 'warehouses') else []
    
    # الفروع/المتاجر
    stores_list = db.execute('''
        SELECT * FROM stores WHERE is_active = 1 ORDER BY name
    ''').fetchall() if table_exists(db, 'stores') else []
    
    # الموظفين
    employees_list = db.execute('''
        SELECT * FROM employees WHERE is_active = 1 ORDER BY name
    ''').fetchall() if table_exists(db, 'employees') else []
    
    return render_template('suppliers_map.html', 
                         suppliers=suppliers_list,
                         competitors=competitors_list,
                         warehouses=warehouses_list,
                         stores=stores_list,
                         employees=employees_list)

@app.route('/api/suppliers', methods=['GET', 'POST'])
@role_required('manager')
def api_suppliers():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        cursor = db.execute('''
            INSERT INTO suppliers (name, phone, address, notes, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (data['name'], data.get('phone'), data.get('address'), data.get('notes'),
              data.get('latitude'), data.get('longitude')))
        supplier_id = cursor.lastrowid
        # حفظ الأرقام الإضافية
        for ph in data.get('phones', []):
            if ph.get('phone'):
                db.execute('INSERT INTO supplier_phones (supplier_id, phone, label, is_primary) VALUES (%s,%s,%s,%s)',
                           (supplier_id, ph['phone'], ph.get('label','جوال'), ph.get('is_primary',0)))
        # حفظ الحسابات
        for acc in data.get('accounts', []):
            if acc.get('account_name'):
                db.execute('INSERT INTO supplier_accounts (supplier_id, account_name, account_number, notes) VALUES (%s,%s,%s,%s)',
                           (supplier_id, acc['account_name'], acc.get('account_number'), acc.get('notes')))
        db.commit()
        return jsonify({'success': True, 'id': supplier_id, 'message': 'تم إضافة المورد'})
    
    suppliers_list = db.execute('SELECT * FROM suppliers WHERE is_active=1 ORDER BY name').fetchall()
    return jsonify([dict(s) for s in suppliers_list])

@app.route('/api/suppliers/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('manager')
def api_supplier(id):
    db = get_db()

    if request.method == 'GET':
        supplier = db.execute('SELECT * FROM suppliers WHERE id=%s', (id,)).fetchone()
        if not supplier:
            return jsonify({}), 404
        result = dict(supplier)
        result['phones'] = [dict(p) for p in db.execute(
            'SELECT * FROM supplier_phones WHERE supplier_id=%s ORDER BY is_primary DESC', (id,)).fetchall()]
        result['accounts'] = [dict(a) for a in db.execute(
            'SELECT * FROM supplier_accounts WHERE supplier_id=%s AND is_active=1', (id,)).fetchall()]
        return jsonify(result)
    
    if request.method == 'PUT':
        data = request.json
        db.execute('''
            UPDATE suppliers SET name=%s, phone=%s, address=%s, notes=%s, latitude=%s, longitude=%s
            WHERE id=%s
        ''', (data['name'], data.get('phone'), data.get('address'), data.get('notes'),
              data.get('latitude'), data.get('longitude'), id))
        # تحديث الأرقام
        db.execute('DELETE FROM supplier_phones WHERE supplier_id=%s', (id,))
        for ph in data.get('phones', []):
            if ph.get('phone'):
                db.execute('INSERT INTO supplier_phones (supplier_id, phone, label, is_primary) VALUES (%s,%s,%s,%s)',
                           (id, ph['phone'], ph.get('label','جوال'), ph.get('is_primary',0)))
        # تحديث الحسابات
        db.execute('DELETE FROM supplier_accounts WHERE supplier_id=%s', (id,))
        for acc in data.get('accounts', []):
            if acc.get('account_name'):
                db.execute('INSERT INTO supplier_accounts (supplier_id, account_name, account_number, notes) VALUES (%s,%s,%s,%s)',
                           (id, acc['account_name'], acc.get('account_number'), acc.get('notes')))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث المورد'})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE suppliers SET is_active=0 WHERE id=%s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف المورد'})

# ═══════════════════════════════════════════════════════════════
# إدارة المنافسين
# ═══════════════════════════════════════════════════════════════

@app.route('/api/competitors', methods=['GET', 'POST'])
@role_required('manager')
def api_competitors():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        db.execute('''
            INSERT INTO competitors (name, type, phone, address, latitude, longitude, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (data['name'], data.get('type', 'سوبرماركت'), data.get('phone'), 
              data.get('address'), data.get('latitude'), data.get('longitude'), data.get('notes')))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة المنافس'})
    
    competitors_list = db.execute('SELECT * FROM competitors WHERE is_active=1 ORDER BY name').fetchall()
    return jsonify([dict(c) for c in competitors_list])

@app.route('/api/competitors/<int:id>', methods=['PUT', 'DELETE'])
@role_required('manager')
def api_competitor(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        db.execute('''
            UPDATE competitors SET name=%s, type=%s, phone=%s, address=%s, latitude=%s, longitude=%s, notes=%s
            WHERE id=%s
        ''', (data['name'], data.get('type', 'سوبرماركت'), data.get('phone'), 
              data.get('address'), data.get('latitude'), data.get('longitude'), data.get('notes'), id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث المنافس'})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE competitors SET is_active=0 WHERE id=%s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف المنافس'})

# ═══════════════════════════════════════════════════════════════
# إدارة المخازن API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/warehouses', methods=['GET', 'POST'])
@role_required('manager')
def api_warehouses():
    db = get_db()
    
    if request.method == 'POST':
        data = request.get_json()
        db.execute('''
            INSERT INTO warehouses (name, address, latitude, longitude)
            VALUES (%s, %s, %s, %s)
        ''', (data['name'], data.get('address'), data.get('latitude'), data.get('longitude')))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة المخزن'})
    
    warehouses_list = db.execute('SELECT * FROM warehouses WHERE is_active=1 ORDER BY name').fetchall()
    return jsonify([dict(w) for w in warehouses_list])

@app.route('/api/warehouses/<int:id>', methods=['PUT', 'DELETE'])
@role_required('manager')
def api_warehouse(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.get_json()
        db.execute('''
            UPDATE warehouses SET name=%s, address=%s, latitude=%s, longitude=%s
            WHERE id=%s
        ''', (data['name'], data.get('address'), data.get('latitude'), data.get('longitude'), id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث المخزن'})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE warehouses SET is_active=0 WHERE id=%s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف المخزن'})

# ═══════════════════════════════════════════════════════════════
# إدارة الفروع API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/stores', methods=['GET', 'POST'])
@role_required('manager')
def api_stores():
    db = get_db()
    
    if request.method == 'POST':
        data = request.get_json()
        db.execute('''
            INSERT INTO stores (name, address, phone, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s)
        ''', (data['name'], data.get('address'), data.get('phone'), data.get('latitude'), data.get('longitude')))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة الفرع'})
    
    stores_list = db.execute('SELECT * FROM stores WHERE is_active=1 ORDER BY name').fetchall()
    return jsonify([dict(s) for s in stores_list])

@app.route('/api/stores/<int:id>', methods=['PUT', 'DELETE'])
@role_required('manager')
def api_store(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.get_json()
        db.execute('''
            UPDATE stores SET name=%s, address=%s, phone=%s, latitude=%s, longitude=%s
            WHERE id=%s
        ''', (data['name'], data.get('address'), data.get('phone'), data.get('latitude'), data.get('longitude'), id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث الفرع'})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE stores SET is_active=0 WHERE id=%s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف الفرع'})

# ═══════════════════════════════════════════════════════════════
# إدارة الموظفين
# ═══════════════════════════════════════════════════════════════

@app.route('/employees')
@role_required('manager')
def employees():
    db = get_db()
    employees_list = db.execute('''
        SELECT * FROM employees WHERE is_active = 1 ORDER BY name
    ''').fetchall()
    return render_template('employees.html', employees=employees_list)

@app.route('/api/employees', methods=['GET', 'POST'])
@role_required('manager')
def api_employees():
    db = get_db()
    
    if request.method == 'POST':
        data = request.get_json()
        db.execute('''
            INSERT INTO employees (name, job_title, phone, address, latitude, longitude, department, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (data['name'], data.get('job_title'), data.get('phone'), data.get('address'), 
              data.get('latitude'), data.get('longitude'), data.get('department'), data.get('notes')))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة الموظف'})
    
    employees_list = db.execute('SELECT * FROM employees WHERE is_active=1 ORDER BY name').fetchall()
    return jsonify([dict(e) for e in employees_list])

@app.route('/api/employees/<int:id>', methods=['PUT', 'DELETE'])
@role_required('manager')
def api_employee(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.get_json()
        db.execute('''
            UPDATE employees SET name=%s, job_title=%s, phone=%s, address=%s, latitude=%s, longitude=%s, department=%s, notes=%s
            WHERE id=%s
        ''', (data['name'], data.get('job_title'), data.get('phone'), data.get('address'),
              data.get('latitude'), data.get('longitude'), data.get('department'), data.get('notes'), id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث الموظف'})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE employees SET is_active=0 WHERE id=%s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف الموظف'})

# ═══════════════════════════════════════════════════════════════
# نظام الإشعارات
# ═══════════════════════════════════════════════════════════════

def create_notification(user_id, title, message, notif_type='info', link=None):
    """إنشاء إشعار جديد"""
    db = get_db()
    db.execute('''
        INSERT INTO notifications (user_id, title, message, type, link)
        VALUES (%s, %s, %s, %s, %s)
    ''', (user_id, title, message, notif_type, link))
    db.commit()

def notify_all_managers(title, message, notif_type='info', link=None):
    """إرسال إشعار لجميع المديرين"""
    db = get_db()
    managers = db.execute("SELECT id FROM users WHERE role='manager' AND is_active=1").fetchall()
    for m in managers:
        create_notification(m['id'], title, message, notif_type, link)

@app.route('/api/notifications')
@login_required
def api_notifications():
    db = get_db()
    notifications = db.execute('''
        SELECT * FROM notifications 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 20
    ''', (session['user_id'],)).fetchall()
    return jsonify([dict(n) for n in notifications])

@app.route('/api/notifications/unread-count')
@login_required
def api_notifications_count():
    db = get_db()
    count = db.execute('''
        SELECT COUNT(*) as count FROM notifications 
        WHERE user_id = %s AND is_read = 0
    ''', (session['user_id'],)).fetchone()['count']
    return jsonify({'count': count})

@app.route('/api/notifications/<int:id>/read', methods=['POST'])
@login_required
def api_notification_read(id):
    db = get_db()
    db.execute('UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s', (id, session['user_id']))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def api_notifications_read_all():
    db = get_db()
    db.execute('UPDATE notifications SET is_read = 1 WHERE user_id = %s', (session['user_id'],))
    db.commit()
    return jsonify({'success': True})

# ═══════════════════════════════════════════════════════════════
# سجل التدقيق
# ═══════════════════════════════════════════════════════════════

def log_action(action, table_name=None, record_id=None, old_data=None, new_data=None):
    """تسجيل إجراء في سجل التدقيق"""
    db = get_db()
    user_id = session.get('user_id')
    ip = request.remote_addr if request else None
    db.execute('''
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_data, new_data, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, action, table_name, record_id, 
          json.dumps(old_data, ensure_ascii=False) if old_data else None,
          json.dumps(new_data, ensure_ascii=False) if new_data else None,
          ip))
    db.commit()

@app.route('/api/audit-log')
@role_required('manager')
def api_audit_log():
    db = get_db()
    logs = db.execute('''
        SELECT a.*, u.full_name as user_name
        FROM audit_log a
        LEFT JOIN users u ON u.id = a.user_id
        ORDER BY a.created_at DESC
        LIMIT 100
    ''').fetchall()
    return jsonify([dict(l) for l in logs])

# ═══════════════════════════════════════════════════════════════
# إدارة الدفعات وتواريخ الصلاحية
# ═══════════════════════════════════════════════════════════════

@app.route('/batches')
@login_required
def batches():
    db = get_db()
    
    # الدفعات مع معلومات المنتج
    batches_list = db.execute('''
        SELECT b.*, p.name as product_name, p.unit,
               s.name as supplier_name,
               CASE 
                   WHEN b.expiry_date < date('now') THEN 'expired'
                   WHEN b.expiry_date <= date('now', '+7 days') THEN 'critical'
                   WHEN b.expiry_date <= date('now', '+30 days') THEN 'warning'
                   ELSE 'ok'
               END as expiry_status,
               julianday(b.expiry_date) - julianday('now') as days_until_expiry
        FROM product_batches b
        JOIN products p ON p.id = b.product_id
        LEFT JOIN supplier_invoices si ON si.id = b.supplier_invoice_id
        LEFT JOIN suppliers s ON s.id = si.supplier_id
        WHERE b.status = 'active' AND b.quantity_remaining > 0
        ORDER BY b.expiry_date ASC
    ''').fetchall()
    
    # إحصائيات
    stats = {
        'total': len(batches_list),
        'expired': len([b for b in batches_list if b['expiry_status'] == 'expired']),
        'critical': len([b for b in batches_list if b['expiry_status'] == 'critical']),
        'warning': len([b for b in batches_list if b['expiry_status'] == 'warning']),
    }
    
    products = db.execute('SELECT id, name FROM products WHERE is_active = 1 ORDER BY name').fetchall()
    
    return render_template('batches.html', batches=batches_list, stats=stats, products=products)

@app.route('/api/batches', methods=['GET', 'POST'])
@login_required
def api_batches():
    db = get_db()
    
    if request.method == 'POST':
        data = request.get_json()
        
        # إنشاء رقم دفعة تلقائي إذا لم يُحدد
        batch_number = data.get('batch_number')
        if not batch_number:
            batch_number = f"LOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor = db.execute('''
            INSERT INTO product_batches 
            (product_id, batch_number, production_date, expiry_date, 
             quantity_received, quantity_remaining, purchase_price, location, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['product_id'],
            batch_number,
            data.get('production_date'),
            data.get('expiry_date'),
            data.get('quantity', 0),
            data.get('quantity', 0),
            data.get('purchase_price'),
            data.get('location'),
            data.get('notes')
        ))
        db.commit()
        
        # تحديث مخزون المنتج
        db.execute('''
            UPDATE products SET current_stock = current_stock + %s WHERE id = %s
        ''', (data.get('quantity', 0), data['product_id']))
        db.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid, 'batch_number': batch_number})
    
    # GET - جلب الدفعات
    batches_list = db.execute('''
        SELECT b.*, p.name as product_name
        FROM product_batches b
        JOIN products p ON p.id = b.product_id
        WHERE b.status = 'active'
        ORDER BY b.expiry_date ASC
    ''').fetchall()
    
    return jsonify([dict(b) for b in batches_list])

@app.route('/api/batches/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_batch(id):
    db = get_db()
    
    if request.method == 'GET':
        batch = db.execute('''
            SELECT b.*, p.name as product_name
            FROM product_batches b
            JOIN products p ON p.id = b.product_id
            WHERE b.id = %s
        ''', (id,)).fetchone()
        return jsonify(dict(batch) if batch else {})
    
    elif request.method == 'PUT':
        data = request.get_json()
        db.execute('''
            UPDATE product_batches 
            SET batch_number=%s, production_date=%s, expiry_date=%s, 
                quantity_remaining=%s, location=%s, notes=%s, status=%s
            WHERE id=%s
        ''', (
            data.get('batch_number'),
            data.get('production_date'),
            data.get('expiry_date'),
            data.get('quantity_remaining'),
            data.get('location'),
            data.get('notes'),
            data.get('status', 'active'),
            id
        ))
        db.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE product_batches SET status = "consumed" WHERE id = %s', (id,))
        db.commit()
        return jsonify({'success': True})

@app.route('/api/batches/expiring')
@login_required
def api_expiring_batches():
    """الدفعات التي ستنتهي صلاحيتها قريباً"""
    db = get_db()
    days = request.args.get('days', 30, type=int)
    
    batches = db.execute('''
        SELECT b.*, p.name as product_name, p.unit,
               julianday(b.expiry_date) - julianday('now') as days_remaining
        FROM product_batches b
        JOIN products p ON p.id = b.product_id
        WHERE b.status = 'active' 
          AND b.quantity_remaining > 0
          AND b.expiry_date <= date('now', '+' || %s || ' days')
          AND b.expiry_date >= date('now')
        ORDER BY b.expiry_date ASC
    ''', (days,)).fetchall()
    
    return jsonify([dict(b) for b in batches])

@app.route('/api/batches/expired')
@login_required
def api_expired_batches():
    """الدفعات المنتهية الصلاحية"""
    db = get_db()
    
    batches = db.execute('''
        SELECT b.*, p.name as product_name, p.unit,
               julianday('now') - julianday(b.expiry_date) as days_expired
        FROM product_batches b
        JOIN products p ON p.id = b.product_id
        WHERE b.status = 'active' 
          AND b.quantity_remaining > 0
          AND b.expiry_date < date('now')
        ORDER BY b.expiry_date ASC
    ''').fetchall()
    
    return jsonify([dict(b) for b in batches])

@app.route('/api/products/<int:product_id>/batches')
@login_required
def api_product_batches(product_id):
    """دفعات منتج معين (FEFO - الأقرب انتهاءً أولاً)"""
    db = get_db()
    
    batches = db.execute('''
        SELECT * FROM product_batches
        WHERE product_id = %s AND status = 'active' AND quantity_remaining > 0
        ORDER BY expiry_date ASC
    ''', (product_id,)).fetchall()
    
    return jsonify([dict(b) for b in batches])

def check_expiry_alerts():
    """فحص الدفعات وإنشاء تنبيهات انتهاء الصلاحية"""
    db = get_db()
    
    # الدفعات التي ستنتهي خلال 7 أيام
    approaching = db.execute('''
        SELECT b.id, b.batch_number, p.name as product_name, b.expiry_date, b.quantity_remaining
        FROM product_batches b
        JOIN products p ON p.id = b.product_id
        WHERE b.status = 'active' 
          AND b.quantity_remaining > 0
          AND b.expiry_date <= date('now', '+7 days')
          AND b.expiry_date > date('now')
          AND b.id NOT IN (
              SELECT batch_id FROM expiry_alerts 
              WHERE alert_type = 'approaching' AND alert_date = date('now')
          )
    ''').fetchall()
    
    for batch in approaching:
        # إنشاء تنبيه
        db.execute('''
            INSERT INTO expiry_alerts (batch_id, alert_type, alert_date)
            VALUES (%s, 'approaching', date('now'))
        ''', (batch['id'],))
        
        # إرسال إشعار للمديرين
        notify_all_managers(
            f"⚠️ صلاحية قريبة: {batch['product_name']}",
            f"الدفعة {batch['batch_number']} ستنتهي في {batch['expiry_date']} - الكمية: {batch['quantity_remaining']}",
            'warning',
            '/batches'
        )
    
    db.commit()

# ═══════════════════════════════════════════════════════════════
# نقاط البيع (POS)
# ═══════════════════════════════════════════════════════════════

@app.route('/pos')
@login_required
def pos():
    db = get_db()
    
    # جلب المنتجات مع الأسعار
    products = db.execute('''
        SELECT p.id, p.name, p.barcode, p.category_id, p.unit, p.current_stock,
               COALESCE(
                   (SELECT pp.price FROM product_prices pp 
                    JOIN price_lists pl ON pl.id = pp.price_list_id 
                    WHERE pp.product_id = p.id AND pl.is_default = 1),
                   0
               ) as price
        FROM products p
        WHERE p.is_active = 1
        ORDER BY p.name
    ''').fetchall()
    
    categories = db.execute('SELECT id, name FROM categories ORDER BY name').fetchall()
    
    return render_template('pos.html', 
                          products=[dict(p) for p in products],
                          categories=categories)

@app.route('/api/pos/invoice', methods=['POST'])
@login_required
def api_pos_invoice():
    """حفظ فاتورة POS"""
    db = get_db()
    data = request.get_json()
    
    # إنشاء رقم فاتورة
    invoice_number = f"POS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # إنشاء الفاتورة
    cursor = db.execute('''
        INSERT INTO pos_invoices 
        (invoice_number, total_amount, discount, payment_method, paid_amount, 
         change_amount, customer_name, customer_phone, created_by, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        invoice_number,
        data.get('total', 0),
        data.get('discount', 0),
        data.get('paymentMethod', 'cash'),
        data.get('paidAmount', 0),
        data.get('change', 0),
        data.get('customer', {}).get('name') if data.get('customer') else None,
        data.get('customer', {}).get('phone') if data.get('customer') else None,
        session.get('user_id'),
        datetime.now().isoformat()
    ))
    invoice_id = cursor.lastrowid
    
    # إضافة بنود الفاتورة وتحديث المخزون
    for item in data.get('items', []):
        db.execute('''
            INSERT INTO pos_invoice_items (invoice_id, product_id, product_name, quantity, price, total)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (invoice_id, item['id'], item['name'], item['qty'], item['price'], item['price'] * item['qty']))
        
        # تحديث المخزون
        db.execute('UPDATE products SET current_stock = current_stock - %s WHERE id = %s', (item['qty'], item['id']))
    
    db.commit()
    
    return jsonify({'success': True, 'invoice_number': invoice_number, 'invoice_id': invoice_id})

@app.route('/api/pos/sync', methods=['POST'])
@login_required  
def api_pos_sync():
    """مزامنة فواتير POS من الأوفلاين"""
    db = get_db()
    data = request.get_json()
    invoices = data.get('invoices', [])
    
    synced = 0
    for invoice_data in invoices:
        if invoice_data.get('synced'):
            continue
            
        # نفس منطق حفظ الفاتورة
        cursor = db.execute('''
            INSERT INTO pos_invoices 
            (invoice_number, total_amount, discount, payment_method, paid_amount, 
             change_amount, customer_name, customer_phone, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            f"POS-{invoice_data.get('number', 0)}",
            invoice_data.get('total', 0),
            invoice_data.get('discount', 0),
            invoice_data.get('paymentMethod', 'cash'),
            invoice_data.get('paidAmount', 0),
            invoice_data.get('change', 0),
            invoice_data.get('customer', {}).get('name') if invoice_data.get('customer') else None,
            invoice_data.get('customer', {}).get('phone') if invoice_data.get('customer') else None,
            session.get('user_id'),
            invoice_data.get('timestamp', datetime.now().isoformat())
        ))
        
        invoice_id = cursor.lastrowid
        for item in invoice_data.get('items', []):
            db.execute('''
                INSERT INTO pos_invoice_items (invoice_id, product_id, product_name, quantity, price, total)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (invoice_id, item['id'], item['name'], item['qty'], item['price'], item['price'] * item['qty']))
        
        synced += 1
    
    db.commit()
    return jsonify({'success': True, 'synced': synced})

@app.route('/api/pos/reports/daily')
@login_required
def api_pos_daily_report():
    """تقرير المبيعات اليومية"""
    db = get_db()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    data = db.execute('''
        SELECT 
            COUNT(*) as total_invoices,
            SUM(total_amount) as total_sales,
            SUM(discount) as total_discount,
            SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END) as cash_sales,
            SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END) as card_sales,
            SUM(CASE WHEN payment_method = 'credit' THEN total_amount ELSE 0 END) as credit_sales
        FROM pos_invoices
        WHERE date(created_at) = %s
    ''', (today,)).fetchone()
    
    return jsonify(dict(data) if data else {})

@app.route('/pos/login')
def pos_login():
    """صفحة تسجيل دخول الكاشير"""
    db = get_db()
    cashiers = db.execute("SELECT id, full_name FROM users WHERE role IN ('cashier', 'manager')").fetchall()
    return render_template('pos_login.html', cashiers=cashiers)

@app.route('/api/pos/verify-pin', methods=['POST'])
def api_pos_verify_pin():
    """التحقق من PIN الكاشير"""
    data = request.get_json()
    user_id = data.get('user_id')
    pin = str(data.get('pin', ''))
    
    if not user_id:
        return jsonify({'success': False, 'message': 'يرجى اختيار المستخدم'})
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = %s', (int(user_id),)).fetchone()
    
    if user:
        # للتبسيط: PIN = 1234 افتراضياً لجميع المستخدمين
        # في الإنتاج يجب إضافة عمود pin_code في جدول users
        if pin == '1234':
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'رمز PIN غير صحيح'})

@app.route('/pos/returns')
@login_required
def pos_returns():
    """صفحة المرتجعات"""
    return render_template('pos_returns.html')

@app.route('/api/pos/invoice/<invoice_number>')
@login_required
def api_pos_get_invoice(invoice_number):
    """جلب تفاصيل فاتورة"""
    db = get_db()
    
    invoice = db.execute('''
        SELECT * FROM pos_invoices WHERE invoice_number = %s OR id = %s
    ''', (invoice_number, invoice_number)).fetchone()
    
    if not invoice:
        return jsonify({'found': False})
    
    items = db.execute('''
        SELECT * FROM pos_invoice_items WHERE invoice_id = %s
    ''', (invoice['id'],)).fetchall()
    
    return jsonify({
        'found': True,
        'invoice': dict(invoice),
        'items': [dict(i) for i in items]
    })

@app.route('/api/pos/return', methods=['POST'])
@login_required
def api_pos_return():
    """معالجة المرتجعات"""
    db = get_db()
    data = request.get_json()
    
    return_number = f"RET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # إنشاء سجل المرتجع
    cursor = db.execute('''
        INSERT INTO pos_returns (return_number, total_amount, refund_method, created_by, created_at)
        VALUES (%s, %s, %s, %s, %s)
    ''', (return_number, data.get('total', 0), data.get('refund_method', 'cash'), 
          session.get('user_id'), datetime.now().isoformat()))
    
    return_id = cursor.lastrowid
    
    # إضافة بنود المرتجع وتحديث المخزون
    for item in data.get('items', []):
        db.execute('''
            INSERT INTO pos_return_items 
            (return_id, invoice_id, product_id, product_name, quantity, price, reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (return_id, item['invoice_id'], item['product_id'], item['product_name'],
              item['return_qty'], item['price'], item.get('reason', '')))
        
        # إرجاع الكمية للمخزون
        db.execute('UPDATE products SET current_stock = current_stock + %s WHERE id = %s', (item['return_qty'], item['product_id']))
    
    db.commit()
    return jsonify({'success': True, 'return_number': return_number})

@app.route('/pos/shift')
@login_required
def pos_shift():
    """صفحة إدارة الورديات"""
    return render_template('pos_shift.html')

@app.route('/api/pos/shift/current')
@login_required
def api_pos_current_shift():
    """جلب الوردية الحالية"""
    db = get_db()
    
    shift = db.execute('''
        SELECT * FROM pos_shifts WHERE user_id = %s AND status = 'open'
        ORDER BY id DESC LIMIT 1
    ''', (session.get('user_id'),)).fetchone()
    
    if not shift:
        return jsonify({'shift': None, 'stats': {}, 'recent_invoices': []})
    
    # إحصائيات الوردية
    stats = db.execute('''
        SELECT 
            COUNT(*) as total_invoices,
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END), 0) as cash_sales,
            COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END), 0) as card_sales
        FROM pos_invoices
        WHERE shift_id = %s
    ''', (shift['id'],)).fetchone()
    
    # آخر الفواتير
    invoices = db.execute('''
        SELECT id, invoice_number, payment_method, total_amount,
               strftime('%H:%M', created_at) as time
        FROM pos_invoices
        WHERE shift_id = %s
        ORDER BY id DESC LIMIT 10
    ''', (shift['id'],)).fetchall()
    
    return jsonify({
        'shift': dict(shift),
        'stats': dict(stats) if stats else {},
        'recent_invoices': [dict(i) for i in invoices]
    })

@app.route('/api/pos/shift/open', methods=['POST'])
@login_required
def api_pos_open_shift():
    """فتح وردية جديدة"""
    db = get_db()
    data = request.get_json()
    
    # التحقق من عدم وجود وردية مفتوحة
    existing = db.execute('''
        SELECT id FROM pos_shifts WHERE user_id = %s AND status = 'open'
    ''', (session.get('user_id'),)).fetchone()
    
    if existing:
        return jsonify({'success': False, 'message': 'يوجد وردية مفتوحة بالفعل'})
    
    db.execute('''
        INSERT INTO pos_shifts (user_id, start_time, opening_balance, status)
        VALUES (%s, %s, %s, 'open')
    ''', (session.get('user_id'), datetime.now().isoformat(), data.get('opening_balance', 0)))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/api/pos/shift/close', methods=['POST'])
@login_required
def api_pos_close_shift():
    """إغلاق الوردية"""
    db = get_db()
    data = request.get_json()
    
    shift = db.execute('''
        SELECT * FROM pos_shifts WHERE user_id = %s AND status = 'open'
    ''', (session.get('user_id'),)).fetchone()
    
    if not shift:
        return jsonify({'success': False, 'message': 'لا توجد وردية مفتوحة'})
    
    # حساب الإجماليات
    stats = db.execute('''
        SELECT 
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END), 0) as cash_sales,
            COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END), 0) as card_sales
        FROM pos_invoices WHERE shift_id = %s
    ''', (shift['id'],)).fetchone()
    
    db.execute('''
        UPDATE pos_shifts SET 
            end_time = %s, closing_balance = %s, total_cash = %s, total_card = %s,
            total_sales = %s, status = 'closed', notes = %s
        WHERE id = %s
    ''', (datetime.now().isoformat(), data.get('closing_balance', 0),
          stats['cash_sales'], stats['card_sales'], stats['total_sales'],
          data.get('notes', ''), shift['id']))
    
    db.commit()
    return jsonify({'success': True})

@app.route('/pos/reports')
@login_required
def pos_reports():
    """صفحة تقارير POS"""
    return render_template('pos_reports.html')

@app.route('/api/pos/reports')
@login_required
def api_pos_reports():
    """API تقارير POS"""
    db = get_db()
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    # الملخص العام
    summary = db.execute('''
        SELECT 
            COUNT(*) as total_invoices,
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(AVG(total_amount), 0) as avg_invoice,
            COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END), 0) as cash_sales,
            COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END), 0) as card_sales,
            COALESCE(SUM(CASE WHEN payment_method = 'bank' THEN total_amount ELSE 0 END), 0) as bank_sales,
            COALESCE(SUM(CASE WHEN payment_method = 'credit' THEN total_amount ELSE 0 END), 0) as credit_sales
        FROM pos_invoices
        WHERE date(created_at) BETWEEN %s AND %s
    ''', (date_from, date_to)).fetchone()
    
    # عدد الأصناف المباعة
    items_count = db.execute('''
        SELECT COALESCE(SUM(pii.quantity), 0) as total_items
        FROM pos_invoice_items pii
        JOIN pos_invoices pi ON pi.id = pii.invoice_id
        WHERE date(pi.created_at) BETWEEN %s AND %s
    ''', (date_from, date_to)).fetchone()
    
    # أكثر المنتجات مبيعاً
    top_products = db.execute('''
        SELECT pii.product_name as name, 
               SUM(pii.quantity) as quantity,
               SUM(pii.total) as total
        FROM pos_invoice_items pii
        JOIN pos_invoices pi ON pi.id = pii.invoice_id
        WHERE date(pi.created_at) BETWEEN %s AND %s
        GROUP BY pii.product_id, pii.product_name
        ORDER BY total DESC
        LIMIT 10
    ''', (date_from, date_to)).fetchall()
    
    # أداء الكاشير
    cashier_stats = db.execute('''
        SELECT u.full_name as name,
               COUNT(*) as invoices,
               COALESCE(SUM(pi.total_amount), 0) as total
        FROM pos_invoices pi
        JOIN users u ON u.id = pi.created_by
        WHERE date(pi.created_at) BETWEEN %s AND %s
        GROUP BY pi.created_by
        ORDER BY total DESC
    ''', (date_from, date_to)).fetchall()
    
    # المبيعات حسب الساعة
    hourly_sales = db.execute('''
        SELECT strftime('%H', created_at) as hour,
               COALESCE(SUM(total_amount), 0) as total
        FROM pos_invoices
        WHERE date(created_at) BETWEEN %s AND %s
        GROUP BY hour
        ORDER BY hour
    ''', (date_from, date_to)).fetchall()
    
    # آخر الفواتير
    recent_invoices = db.execute('''
        SELECT pi.*, u.full_name as cashier,
               strftime('%Y-%m-%d %H:%M', pi.created_at) as date,
               (SELECT COUNT(*) FROM pos_invoice_items WHERE invoice_id = pi.id) as items_count
        FROM pos_invoices pi
        LEFT JOIN users u ON u.id = pi.created_by
        WHERE date(pi.created_at) BETWEEN %s AND %s
        ORDER BY pi.id DESC
        LIMIT 50
    ''', (date_from, date_to)).fetchall()
    
    return jsonify({
        'summary': {
            **dict(summary),
            'total_items': items_count['total_items'] if items_count else 0
        },
        'payment_breakdown': {
            'cash': summary['cash_sales'],
            'card': summary['card_sales'],
            'bank': summary['bank_sales'],
            'credit': summary['credit_sales']
        },
        'top_products': [dict(p) for p in top_products],
        'cashier_stats': [dict(c) for c in cashier_stats],
        'hourly_sales': [dict(h) for h in hourly_sales],
        'recent_invoices': [dict(i) for i in recent_invoices]
    })

# ═══════════════════════════════════════════════════════════════
# إدارة الأقسام
# ═══════════════════════════════════════════════════════════════

@app.route('/categories')
@role_required('manager')
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
@role_required('manager')
def api_categories():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        parent_id = data.get('parent_id')
        if parent_id == '' or parent_id == 0:
            parent_id = None
        db.execute('''
            INSERT INTO categories (name, parent_id, sort_order)
            VALUES (%s, %s, %s)
        ''', (data['name'], parent_id, data.get('sort_order', 0)))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة القسم'})
    
    categories_list = db.execute('SELECT * FROM categories ORDER BY parent_id NULLS FIRST, sort_order, name').fetchall()
    return jsonify([dict(c) for c in categories_list])

@app.route('/api/categories/<int:id>', methods=['PUT', 'DELETE'])
@role_required('manager')
def api_category(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        parent_id = data.get('parent_id')
        if parent_id == '' or parent_id == 0:
            parent_id = None
        db.execute('''
            UPDATE categories SET name=%s, parent_id=%s, sort_order=%s
            WHERE id=%s
        ''', (data['name'], parent_id, data.get('sort_order', 0), id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث القسم'})
    
    elif request.method == 'DELETE':
        # التحقق من وجود أصناف أو أقسام فرعية
        has_products = db.execute('SELECT COUNT(*) as count FROM products WHERE category_id = %s', (id,)).fetchone()['count']
        has_children = db.execute('SELECT COUNT(*) as count FROM categories WHERE parent_id = %s', (id,)).fetchone()['count']
        
        if has_products > 0:
            return jsonify({'success': False, 'message': f'لا يمكن حذف القسم - يحتوي على {has_products} صنف'})
        if has_children > 0:
            return jsonify({'success': False, 'message': f'لا يمكن حذف القسم - يحتوي على {has_children} قسم فرعي'})
        
        db.execute('DELETE FROM categories WHERE id=%s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف القسم'})

# ═══════════════════════════════════════════════════════════════
# إدارة الوحدات
# ═══════════════════════════════════════════════════════════════

@app.route('/units')
@role_required('manager')
def units():
    db = get_db()
    units_list = db.execute('SELECT * FROM units WHERE is_active = 1 ORDER BY name').fetchall()
    return render_template('units.html', units=units_list)

@app.route('/api/units', methods=['GET', 'POST'])
@role_required('manager')
def api_units():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        # التحقق من عدم التكرار
        existing = db.execute('SELECT id FROM units WHERE name = %s', (data['name'],)).fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'الوحدة موجودة مسبقاً'})
        
        db.execute('INSERT INTO units (name, symbol) VALUES (%s, %s)',
                   (data['name'], data.get('symbol', '')))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة الوحدة'})
    
    units_list = db.execute('SELECT * FROM units WHERE is_active = 1 ORDER BY name').fetchall()
    return jsonify([dict(u) for u in units_list])

@app.route('/api/units/<int:id>', methods=['PUT', 'DELETE'])
@role_required('manager')
def api_unit(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        db.execute('UPDATE units SET name=%s, symbol=%s WHERE id=%s',
                   (data['name'], data.get('symbol', ''), id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث الوحدة'})
    
    elif request.method == 'DELETE':
        # التحقق من عدم استخدام الوحدة
        used = db.execute('SELECT COUNT(*) as count FROM product_units WHERE unit_id = %s', (id,)).fetchone()['count']
        if used > 0:
            return jsonify({'success': False, 'message': f'لا يمكن حذف الوحدة - مستخدمة في {used} صنف'})
        
        db.execute('UPDATE units SET is_active = 0 WHERE id = %s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف الوحدة'})

# ═══════════════════════════════════════════════════════════════
# ماسح الباركود
# ═══════════════════════════════════════════════════════════════

@app.route('/barcode-scanner')
@login_required
def barcode_scanner():
    db = get_db()
    categories = db.execute('SELECT * FROM categories ORDER BY name').fetchall()
    units = db.execute('SELECT * FROM units WHERE is_active = 1 ORDER BY name').fetchall()
    return render_template('barcode_scanner.html', categories=categories, units=units)

@app.route('/api/barcode/<barcode>')
@login_required
def api_barcode_lookup(barcode):
    db = get_db()
    
    # البحث في الأصناف (الباركود الرئيسي)
    product = db.execute('''
        SELECT p.*, c.name as category_name,
               p.sell_price as price
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.barcode = %s AND p.is_active = 1
    ''', (barcode,)).fetchone()
    
    if product:
        return jsonify({'found': True, 'product': dict(product)})
    
    # البحث في وحدات الأصناف
    product_unit = db.execute('''
        SELECT p.*, c.name as category_name, pu.price, pu.barcode as unit_barcode
        FROM product_units pu
        JOIN products p ON p.id = pu.product_id
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE pu.barcode = %s AND p.is_active = 1
    ''', (barcode,)).fetchone()
    
    if product_unit:
        return jsonify({'found': True, 'product': dict(product_unit)})
    
    # البحث في جدول الباركودات المتعددة
    multi_barcode = db.execute('''
        SELECT p.*, c.name as category_name,
               pb.unit as barcode_unit, pb.pack_size as barcode_pack_size,
               pb.cost_price as barcode_cost, pb.sell_price as barcode_sell
        FROM product_barcodes pb
        JOIN products p ON p.id = pb.product_id
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE pb.barcode = %s AND p.is_active = 1
    ''', (barcode,)).fetchone()
    
    if multi_barcode:
        result = dict(multi_barcode)
        # Use barcode-specific price and unit
        result['unit'] = result.pop('barcode_unit', result.get('unit'))
        result['pack_size'] = result.pop('barcode_pack_size', 1)
        if result.get('barcode_sell'):
            result['sell_price'] = result.pop('barcode_sell')
            result['price'] = result['sell_price']
        if result.get('barcode_cost'):
            result['cost_price'] = result.pop('barcode_cost')
        return jsonify({'found': True, 'product': result, 'source': 'barcode_unit'})
    
    # البحث في أصناف الموردين
    supplier_product = db.execute('''
        SELECT sp.*, p.name, p.id as product_id, p.current_stock, p.unit,
               c.name as category_name, s.name as supplier_name
        FROM supplier_products sp
        JOIN products p ON p.id = sp.product_id
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN suppliers s ON s.id = sp.supplier_id
        WHERE sp.supplier_barcode = %s AND sp.is_active = 1
    ''', (barcode,)).fetchone()
    
    if supplier_product:
        return jsonify({'found': True, 'product': dict(supplier_product), 'source': 'supplier'})
    
    return jsonify({'found': False})

@app.route('/api/products/<int:product_id>/barcodes')
@login_required
def api_product_barcodes(product_id):
    db = get_db()
    barcodes = db.execute('''
        SELECT * FROM product_barcodes WHERE product_id = %s ORDER BY pack_size
    ''', (product_id,)).fetchall()
    return jsonify([dict(b) for b in barcodes])

# ═══════════════════════════════════════════════════════════════
# إدارة الأصناف
# ═══════════════════════════════════════════════════════════════

@app.route('/products')
@role_required('manager')
def products():
    db = get_db()
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('q', '').strip()
    cat_filter = request.args.get('cat', '', type=str)
    brand_filter = request.args.get('brand', '').strip()
    
    # Build query
    where = ['p.is_active = 1']
    params = []
    
    if search:
        where.append("(p.name LIKE %s OR p.barcode LIKE %s OR p.product_code LIKE %s OR p.brand LIKE %s)")
        s = f'%{search}%'
        params.extend([s, s, s, s])
    
    if cat_filter:
        where.append("p.category_id = %s")
        params.append(cat_filter)
    
    if brand_filter:
        where.append("p.brand = %s")
        params.append(brand_filter)
    
    where_sql = ' AND '.join(where)
    
    # Total count
    total = db.execute(f'SELECT COUNT(*) FROM products p WHERE {where_sql}', params).fetchone()['count']
    total_pages = (total + per_page - 1) // per_page
    
    # Get page
    offset = (page - 1) * per_page
    products_list = db.execute(f'''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE {where_sql}
        ORDER BY p.category_id, p.name
        LIMIT %s OFFSET %s
    ''', params + [per_page, offset]).fetchall()
    
    categories = db.execute('SELECT * FROM categories ORDER BY id').fetchall()
    
    # Get unique brands for filter
    brands = db.execute('SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND is_active=1 ORDER BY brand').fetchall()
    
    try:
        units_list = db.execute('SELECT * FROM units WHERE is_active = 1 ORDER BY name').fetchall()
    except:
        units_list = []
    
    return render_template('products.html', 
                         products=products_list, categories=categories, units=units_list,
                         brands=brands, page=page, per_page=per_page, total=total, 
                         total_pages=total_pages, search=search, cat_filter=cat_filter,
                         brand_filter=brand_filter)

@app.route('/api/products', methods=['GET', 'POST'])
@role_required('manager')
def api_products():
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        cursor = db.execute('''
            INSERT INTO products (name, name_en, receipt_name, barcode, product_code, brand, category_id, unit, pack_size, cost_price, sell_price, min_stock, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['name'], data.get('name_en'), data.get('receipt_name'),
            data.get('barcode'), data.get('product_code'), data.get('brand'),
            data.get('category_id'), data.get('unit', 'حبه'),
            data.get('pack_size', 1), data.get('cost_price', 0), data.get('sell_price', 0),
            data.get('min_stock', 0), data.get('notes')
        ))
        product_id = cursor.lastrowid
        
        # حفظ الوحدات
        units = data.get('units', [])
        for unit_data in units:
            db.execute('''
                INSERT INTO product_units (product_id, unit_id, conversion_factor, barcode, price, is_default)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                product_id, unit_data['unit_id'],
                unit_data.get('conversion_factor', 1),
                unit_data.get('barcode', ''),
                unit_data.get('price', 0),
                1 if unit_data.get('is_default') else 0
            ))
        
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة الصنف', 'id': product_id})
    
    products_list = db.execute('''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.is_active = 1
        ORDER BY p.name
    ''').fetchall()
    return jsonify([dict(p) for p in products_list])

@app.route('/api/products/<int:id>', methods=['PUT', 'DELETE'])
@role_required('manager')
def api_product(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        db.execute('''
            UPDATE products SET name=%s, name_en=%s, receipt_name=%s, barcode=%s,
                   category_id=%s, unit=%s, min_stock=%s, notes=%s
            WHERE id=%s
        ''', (
            data['name'], data.get('name_en'), data.get('receipt_name'),
            data.get('barcode'), data.get('category_id'), data.get('unit'),
            data.get('min_stock', 0), data.get('notes'), id
        ))
        
        # تحديث الوحدات
        units = data.get('units', [])
        if units:
            # حذف الوحدات القديمة وإضافة الجديدة
            db.execute('DELETE FROM product_units WHERE product_id = %s', (id,))
            for unit_data in units:
                db.execute('''
                    INSERT INTO product_units (product_id, unit_id, conversion_factor, barcode, price, is_default)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    id, unit_data['unit_id'],
                    unit_data.get('conversion_factor', 1),
                    unit_data.get('barcode', ''),
                    unit_data.get('price', 0),
                    1 if unit_data.get('is_default') else 0
                ))
        
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث الصنف'})
    
    elif request.method == 'DELETE':
        db.execute('UPDATE products SET is_active=0 WHERE id=%s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف الصنف'})

# ═══════════════════════════════════════════════════════════════
# وحدات الصنف المتعددة
# ═══════════════════════════════════════════════════════════════

@app.route('/api/products/<int:product_id>/units', methods=['GET', 'POST'])
@role_required('manager')
def api_product_units(product_id):
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        unit_id = data.get('unit_id')
        
        # التحقق من عدم التكرار
        existing = db.execute(
            'SELECT id FROM product_units WHERE product_id = %s AND unit_id = %s',
            (product_id, unit_id)
        ).fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'هذه الوحدة مضافة مسبقاً لهذا الصنف'})
        
        # إذا كانت أول وحدة، اجعلها افتراضية
        count = db.execute('SELECT COUNT(*) as count FROM product_units WHERE product_id = %s', (product_id,)).fetchone()['count']
        is_default = 1 if count == 0 else (1 if data.get('is_default') else 0)
        
        # إذا تم تعيينها كافتراضية، ألغِ الافتراضي السابق
        if is_default:
            db.execute('UPDATE product_units SET is_default = 0 WHERE product_id = %s', (product_id,))
        
        db.execute('''
            INSERT INTO product_units (product_id, unit_id, conversion_factor, barcode, price, is_default)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            product_id, unit_id,
            data.get('conversion_factor', 1),
            data.get('barcode', ''),
            data.get('price', 0),
            is_default
        ))
        db.commit()
        return jsonify({'success': True, 'message': 'تم إضافة الوحدة للصنف'})
    
    # GET - جلب وحدات الصنف
    units = db.execute('''
        SELECT pu.*, u.name as unit_name, u.symbol
        FROM product_units pu
        JOIN units u ON u.id = pu.unit_id
        WHERE pu.product_id = %s
        ORDER BY pu.is_default DESC, u.name
    ''', (product_id,)).fetchall()
    return jsonify([dict(u) for u in units])

@app.route('/api/product-units/<int:id>', methods=['PUT', 'DELETE'])
@role_required('manager')
def api_product_unit(id):
    db = get_db()
    
    if request.method == 'PUT':
        data = request.json
        
        # إذا تم تعيينها كافتراضية، ألغِ الافتراضي السابق
        if data.get('is_default'):
            product_id = db.execute('SELECT product_id FROM product_units WHERE id = %s', (id,)).fetchone()['count']
            db.execute('UPDATE product_units SET is_default = 0 WHERE product_id = %s', (product_id,))
        
        db.execute('''
            UPDATE product_units SET conversion_factor=%s, barcode=%s, price=%s, is_default=%s
            WHERE id=%s
        ''', (
            data.get('conversion_factor', 1),
            data.get('barcode', ''),
            data.get('price', 0),
            1 if data.get('is_default') else 0,
            id
        ))
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث الوحدة'})
    
    elif request.method == 'DELETE':
        # التحقق من أنها ليست الوحدة الوحيدة
        pu = db.execute('SELECT product_id, is_default FROM product_units WHERE id = %s', (id,)).fetchone()
        if pu:
            count = db.execute('SELECT COUNT(*) as count FROM product_units WHERE product_id = %s', (pu['product_id'],)).fetchone()['count']
            if count <= 1:
                return jsonify({'success': False, 'message': 'لا يمكن حذف الوحدة الوحيدة للصنف'})
            
            db.execute('DELETE FROM product_units WHERE id = %s', (id,))
            
            # إذا كانت الافتراضية، اجعل أخرى افتراضية
            if pu['is_default']:
                db.execute('''
                    UPDATE product_units SET is_default = 1 
                    WHERE product_id = %s AND id = (SELECT MIN(id) FROM product_units WHERE product_id = %s)
                ''', (pu['product_id'], pu['product_id']))
            
            db.commit()
        return jsonify({'success': True, 'message': 'تم حذف الوحدة'})

# ═══════════════════════════════════════════════════════════════
# ربط أسماء المورد + إعدادات الفرز
# ═══════════════════════════════════════════════════════════════

@app.route('/supplier-products')
@role_required('manager')
def supplier_products():
    db = get_db()
    supplier_id = request.args.get('supplier_id', type=int)
    
    query = '''
        SELECT sp.*, s.name as supplier_name,
               p.name as product_name,
               (SELECT COUNT(*) FROM sorting_rules WHERE supplier_product_id = sp.id) as linked_count
        FROM supplier_products sp
        JOIN suppliers s ON s.id = sp.supplier_id
        LEFT JOIN products p ON p.id = sp.product_id
    '''
    if supplier_id:
        query += ' WHERE sp.supplier_id = %s'
        items = db.execute(query + ' ORDER BY sp.supplier_product_name', (supplier_id,)).fetchall()
    else:
        items = db.execute(query + ' ORDER BY s.name, sp.supplier_product_name').fetchall()
    
    suppliers = db.execute('SELECT * FROM suppliers WHERE is_active=1 ORDER BY name').fetchall()
    products_list = db.execute('SELECT * FROM products WHERE is_active=1 ORDER BY name').fetchall()
    units_list = db.execute('SELECT * FROM units WHERE is_active=1 ORDER BY name').fetchall()
    
    return render_template('supplier_products.html', 
                         items=items, suppliers=suppliers, 
                         products=products_list, selected_supplier=supplier_id,
                         units=units_list)

@app.route('/api/supplier-products', methods=['POST'])
@role_required('manager')
def api_supplier_products():
    db = get_db()
    data = request.json
    
    allowed_products = data.get('allowed_products', [])
    primary_product_id = allowed_products[0] if allowed_products else None
    
    cursor = db.execute('''
        INSERT INTO supplier_products (supplier_id, supplier_product_name, supplier_product_code, 
                                       supplier_barcode, supplier_unit, product_id, pack_size, 
                                       purchase_price, min_order_qty, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        data['supplier_id'], data['supplier_product_name'], 
        data.get('supplier_product_code'), data.get('supplier_barcode'),
        data.get('supplier_unit', 'كرتون'), primary_product_id,
        data.get('pack_size', 1), data.get('purchase_price', 0),
        data.get('min_order_qty', 1), data.get('notes')
    ))
    supplier_product_id = cursor.lastrowid
    
    for product_id in allowed_products:
        db.execute('''
            INSERT OR IGNORE INTO sorting_rules (supplier_product_id, allowed_product_id)
            VALUES (%s, %s)
        ''', (supplier_product_id, product_id))
    
    db.commit()
    msg = f'تم إضافة الصنف مع ربط {len(allowed_products)} أصناف' if allowed_products else 'تم إضافة الصنف'
    return jsonify({'success': True, 'id': supplier_product_id, 'message': msg})

@app.route('/api/supplier-products/<int:id>/link', methods=['POST'])
@role_required('manager')
def api_supplier_product_link(id):
    """ربط صنف المورد بصنف داخلي"""
    db = get_db()
    data = request.json
    product_id = data.get('product_id')
    db.execute('UPDATE supplier_products SET product_id = %s WHERE id = %s', (product_id, id))
    db.commit()
    return jsonify({'success': True, 'message': 'تم تحديث الربط'})

@app.route('/api/sorting-rules/<int:supplier_product_id>', methods=['GET', 'POST'])
@role_required('manager')
def api_sorting_rules(supplier_product_id):
    db = get_db()
    
    if request.method == 'POST':
        data = request.json
        # حذف القواعد القديمة
        db.execute('DELETE FROM sorting_rules WHERE supplier_product_id = %s', (supplier_product_id,))
        # إضافة الجديدة
        for product_id in data.get('allowed_products', []):
            db.execute('''
                INSERT INTO sorting_rules (supplier_product_id, allowed_product_id)
                VALUES (%s, %s)
            ''', (supplier_product_id, product_id))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حفظ إعدادات الفرز'})
    
    rules = db.execute('''
        SELECT sr.*, p.name as product_name
        FROM sorting_rules sr
        JOIN products p ON p.id = sr.allowed_product_id
        WHERE sr.supplier_product_id = %s
    ''', (supplier_product_id,)).fetchall()
    
    return jsonify([dict(r) for r in rules])

@app.route('/api/supplier-products/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('manager')
def api_supplier_product(id):
    db = get_db()
    
    if request.method == 'GET':
        item = db.execute('''
            SELECT sp.*, s.name as supplier_name,
                   p.name as product_name
            FROM supplier_products sp
            JOIN suppliers s ON s.id = sp.supplier_id
            LEFT JOIN products p ON p.id = sp.product_id
            WHERE sp.id = %s
        ''', (id,)).fetchone()
        
        if not item:
            return jsonify({'success': False, 'message': 'الصنف غير موجود'}), 404
        
        # جلب قواعد الفرز
        rules = db.execute('''
            SELECT allowed_product_id FROM sorting_rules WHERE supplier_product_id = %s
        ''', (id,)).fetchall()
        
        result = dict(item)
        result['allowed_products'] = [r['allowed_product_id'] for r in rules]
        return jsonify(result)
    
    elif request.method == 'PUT':
        data = request.json
        
        # تحديث بيانات صنف المورد
        db.execute('''
            UPDATE supplier_products SET 
                supplier_product_name = %s,
                supplier_product_code = %s,
                supplier_barcode = %s,
                supplier_unit = %s,
                pack_size = %s,
                purchase_price = %s,
                min_order_qty = %s,
                notes = %s
            WHERE id = %s
        ''', (
            data['supplier_product_name'],
            data.get('supplier_product_code'),
            data.get('supplier_barcode'),
            data.get('supplier_unit', 'كرتون'),
            data.get('pack_size', 1),
            data.get('purchase_price', 0),
            data.get('min_order_qty', 1),
            data.get('notes'),
            id
        ))
        
        # تحديث قواعد الفرز
        allowed_products = data.get('allowed_products', [])
        if allowed_products:
            db.execute('DELETE FROM sorting_rules WHERE supplier_product_id = %s', (id,))
            # تحديث الصنف الرئيسي
            db.execute('UPDATE supplier_products SET product_id = %s WHERE id = %s', (allowed_products[0], id))
            for product_id in allowed_products:
                db.execute('''
                    INSERT INTO sorting_rules (supplier_product_id, allowed_product_id)
                    VALUES (%s, %s)
                ''', (id, product_id))
        
        db.commit()
        return jsonify({'success': True, 'message': 'تم تحديث الصنف'})
    
    elif request.method == 'DELETE':
        # التحقق من عدم استخدامه في فواتير
        used = db.execute('''
            SELECT COUNT(*) as count FROM supplier_invoice_items WHERE supplier_product_id = %s
        ''', (id,)).fetchone()
        
        if used['count'] > 0:
            return jsonify({'success': False, 'message': 'لا يمكن حذف هذا الصنف لأنه مستخدم في فواتير'})
        
        db.execute('DELETE FROM sorting_rules WHERE supplier_product_id = %s', (id,))
        db.execute('DELETE FROM supplier_products WHERE id = %s', (id,))
        db.commit()
        return jsonify({'success': True, 'message': 'تم حذف الصنف'})

# ═══════════════════════════════════════════════════════════════
# أسعار الموردين + المقارنة
# ═══════════════════════════════════════════════════════════════

@app.route('/supplier-prices')
@role_required('manager')
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
@role_required('manager')
def api_supplier_prices():
    db = get_db()
    data = request.json
    
    # تحديث أو إضافة السعر
    existing = db.execute('''
        SELECT id FROM supplier_prices 
        WHERE supplier_id = %s AND product_id = %s
    ''', (data['supplier_id'], data['product_id'])).fetchone()
    
    if existing:
        db.execute('''
            UPDATE supplier_prices SET unit_price=%s, pack_price=%s, pack_size=%s, effective_date=%s
            WHERE id=%s
        ''', (data['unit_price'], data.get('pack_price'), data.get('pack_size', 1), 
              datetime.now().isoformat(), existing['id']))
    else:
        db.execute('''
            INSERT INTO supplier_prices (supplier_id, product_id, unit_price, pack_price, pack_size)
            VALUES (%s, %s, %s, %s, %s)
        ''', (data['supplier_id'], data['product_id'], data['unit_price'],
              data.get('pack_price'), data.get('pack_size', 1)))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم حفظ السعر'})

# ═══════════════════════════════════════════════════════════════
# أسعار المنافسين
# ═══════════════════════════════════════════════════════════════

@app.route('/competitor-prices')
@role_required('manager')
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

@app.route('/api/competitor-prices', methods=['POST'])
@role_required('manager')
def api_competitor_prices():
    db = get_db()
    data = request.json
    
    db.execute('''
        INSERT INTO competitor_prices (competitor_id, product_id, price)
        VALUES (%s, %s, %s)
    ''', (data['competitor_id'], data['product_id'], data['price']))
    db.commit()
    
    return jsonify({'success': True, 'message': 'تم حفظ السعر'})

# ═══════════════════════════════════════════════════════════════
# تسعيرات البيع
# ═══════════════════════════════════════════════════════════════

@app.route('/pricing')
@role_required('manager')
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
@role_required('manager')
def api_product_prices():
    db = get_db()
    data = request.json
    
    # تحديث أو إضافة السعر
    existing = db.execute('''
        SELECT id FROM product_prices 
        WHERE product_id = %s AND price_list_id = %s
    ''', (data['product_id'], data['price_list_id'])).fetchone()
    
    if existing:
        db.execute('UPDATE product_prices SET price=%s WHERE id=%s', (data['price'], existing['id']))
    else:
        db.execute('''
            INSERT INTO product_prices (product_id, price_list_id, price)
            VALUES (%s, %s, %s)
        ''', (data['product_id'], data['price_list_id'], data['price']))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم حفظ السعر'})

# ═══════════════════════════════════════════════════════════════
# فواتير المورد
# ═══════════════════════════════════════════════════════════════

@app.route('/supplier-invoices')
@role_required('manager', 'agent')
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
@role_required('manager', 'agent')
def view_supplier_invoice(id):
    db = get_db()
    
    invoice = db.execute('''
        SELECT si.*, s.name as supplier_name, s.phone as supplier_phone,
               u.full_name as created_by_name
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        JOIN users u ON u.id = si.created_by
        WHERE si.id = %s
    ''', (id,)).fetchone()
    
    if not invoice:
        flash('الفاتورة غير موجودة', 'error')
        return redirect(url_for('supplier_invoices'))
    
    items = db.execute('''
        SELECT sii.*, sp.supplier_product_name, sp.pack_size, p.name as product_name
        FROM supplier_invoice_items sii
        JOIN supplier_products sp ON sp.id = sii.supplier_product_id
        JOIN products p ON p.id = sp.product_id
        WHERE sii.invoice_id = %s
    ''', (id,)).fetchall()
    
    return render_template('supplier_invoice_view.html', invoice=invoice, items=items)

@app.route('/api/supplier-invoices/<int:id>/pay', methods=['POST'])
@role_required('manager', 'agent')
def pay_supplier_invoice(id):
    db = get_db()
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get('amount', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'المبلغ غير صحيح'})
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'المبلغ غير صحيح'})
    
    invoice = db.execute(
        'SELECT id, total_amount, paid_amount FROM supplier_invoices WHERE id = %s',
        (id,)
    ).fetchone()
    
    if not invoice:
        return jsonify({'success': False, 'message': 'الفاتورة غير موجودة'}), 404
    
    remaining = float(invoice['total_amount']) - float(invoice['paid_amount'])
    if remaining <= 0:
        return jsonify({'success': False, 'message': 'الفاتورة مسددة بالكامل'})
    
    if amount > remaining:
        return jsonify({'success': False, 'message': f'المبلغ أكبر من المتبقي ({remaining:,.0f} ريال)'})
    
    db.execute('UPDATE supplier_invoices SET paid_amount = paid_amount + %s WHERE id = %s', (amount, id))
    db.commit()
    
    return jsonify({'success': True, 'message': f'تم تسجيل دفعة {amount:,.0f} ريال'})

@app.route('/supplier-invoices/new', methods=['GET', 'POST'])
@role_required('manager', 'agent')
def new_supplier_invoice():
    db = get_db()
    
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        items = data.get('items') or []
        
        try:
            supplier_id = int(data.get('supplier_id'))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'المورد غير صحيح'})
        
        if not data.get('invoice_date'):
            return jsonify({'success': False, 'message': 'تاريخ الفاتورة مطلوب'})
        
        try:
            total_amount = float(data.get('total_amount', 0))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'إجمالي الفاتورة غير صحيح'})
        
        if total_amount <= 0:
            return jsonify({'success': False, 'message': 'إجمالي الفاتورة يجب أن يكون أكبر من صفر'})
        
        if not items:
            return jsonify({'success': False, 'message': 'يجب إضافة بند واحد على الأقل'})
        
        supplier = db.execute(
            'SELECT id FROM suppliers WHERE id = %s AND is_active = 1',
            (supplier_id,)
        ).fetchone()
        
        if not supplier:
            return jsonify({'success': False, 'message': 'المورد غير موجود أو غير نشط'})
        
        # إنشاء رقم فاتورة تلقائي
        last = db.execute('SELECT MAX(id) FROM supplier_invoices').fetchone()['count'] or 0
        invoice_number = f"SI-{datetime.now().strftime('%Y%m')}-{last+1:04d}"
        
        cursor = db.execute('''
            INSERT INTO supplier_invoices (invoice_number, supplier_id, invoice_date, total_amount, notes, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            invoice_number, supplier_id, data['invoice_date'],
            total_amount, data.get('notes'), session['user_id']
        ))
        invoice_id = cursor.lastrowid
        
        # إضافة البنود
        for item in items:
            try:
                supplier_product_id = int(item['supplier_product_id'])
                quantity = float(item['quantity'])
                unit_price = float(item['unit_price'])
                line_total = float(item['total_price'])
            except (KeyError, TypeError, ValueError):
                return jsonify({'success': False, 'message': 'بيانات البنود غير صحيحة'})
            
            if quantity <= 0 or unit_price < 0 or line_total < 0:
                return jsonify({'success': False, 'message': 'قيم البنود غير صحيحة'})
            
            supplier_product = db.execute(
                'SELECT id FROM supplier_products WHERE id = %s AND supplier_id = %s',
                (supplier_product_id, supplier_id)
            ).fetchone()
            
            if not supplier_product:
                return jsonify({'success': False, 'message': 'أحد أصناف المورد غير صحيح'})
            
            db.execute('''
                INSERT INTO supplier_invoice_items (invoice_id, supplier_product_id, quantity, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s)
            ''', (invoice_id, supplier_product_id, quantity, unit_price, line_total))
        
        db.commit()
        return jsonify({'success': True, 'id': invoice_id, 'invoice_number': invoice_number})
    
    suppliers = db.execute('SELECT * FROM suppliers WHERE is_active=1 ORDER BY name').fetchall()
    return render_template('supplier_invoice_form.html', suppliers=suppliers)

@app.route('/api/supplier/<int:supplier_id>/products')
@role_required('manager', 'agent')
def api_supplier_product_list(supplier_id):
    db = get_db()
    items = db.execute('''
        SELECT sp.*, p.name as product_name
        FROM supplier_products sp
        JOIN products p ON p.id = sp.product_id
        WHERE sp.supplier_id = %s
        ORDER BY sp.supplier_product_name
    ''', (supplier_id,)).fetchall()
    return jsonify([dict(i) for i in items])

# ═══════════════════════════════════════════════════════════════
# فاتورة المندوب (الفرز)
# ═══════════════════════════════════════════════════════════════

@app.route('/agent-invoices')
@role_required('manager', 'agent')
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
@role_required('manager', 'agent')
def sort_invoice(supplier_invoice_id):
    db = get_db()

    invoice = db.execute('''
        SELECT si.*, s.name as supplier_name
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        WHERE si.id = %s
    ''', (supplier_invoice_id,)).fetchone()

    if not invoice:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'فاتورة المورد غير موجودة'}), 404
        flash('فاتورة المورد غير موجودة', 'error')
        return redirect(url_for('agent_invoices'))
    
    if request.method == 'POST':
        if invoice['status'] != 'pending':
            return jsonify({'success': False, 'message': 'لا يمكن فرز فاتورة ليست في حالة انتظار'})
        
        data = request.get_json(silent=True) or {}
        raw_items = data.get('items') or []
        
        if not raw_items:
            return jsonify({'success': False, 'message': 'يجب إضافة بند واحد على الأقل للفرز'})
        
        existing_processing = db.execute('''
            SELECT id FROM agent_invoices
            WHERE supplier_invoice_id = %s AND status IN ('draft', 'submitted')
        ''', (supplier_invoice_id,)).fetchone()
        
        if existing_processing:
            return jsonify({'success': False, 'message': 'يوجد بالفعل فاتورة فرز نشطة لهذه الفاتورة'})
        
        parsed_items = []
        requested_quantities = {}
        
        for item in raw_items:
            try:
                supplier_invoice_item_id = int(item['supplier_invoice_item_id'])
                product_id = int(item['product_id'])
                quantity = float(item['quantity'])
            except (KeyError, TypeError, ValueError):
                return jsonify({'success': False, 'message': 'بيانات الفرز غير صحيحة'})
            
            if quantity <= 0:
                return jsonify({'success': False, 'message': 'كمية الفرز يجب أن تكون أكبر من صفر'})
            
            parsed_items.append({
                'supplier_invoice_item_id': supplier_invoice_item_id,
                'product_id': product_id,
                'quantity': quantity,
            })
            requested_quantities[supplier_invoice_item_id] = requested_quantities.get(supplier_invoice_item_id, 0) + quantity
        
        supplier_items_map = {}
        for supplier_invoice_item_id, requested_qty in requested_quantities.items():
            supplier_item = db.execute('''
                SELECT id, supplier_product_id, quantity, sorted_quantity
                FROM supplier_invoice_items
                WHERE id = %s AND invoice_id = %s
            ''', (supplier_invoice_item_id, supplier_invoice_id)).fetchone()
            
            if not supplier_item:
                return jsonify({'success': False, 'message': 'أحد بنود الفاتورة غير موجود'})
            
            available_qty = float(supplier_item['quantity']) - float(supplier_item['sorted_quantity'])
            if requested_qty > available_qty:
                return jsonify({'success': False, 'message': f'الكمية المطلوبة أكبر من المتاح ({available_qty:,.2f})'})
            
            supplier_items_map[supplier_invoice_item_id] = supplier_item
        
        for item in parsed_items:
            supplier_item = supplier_items_map[item['supplier_invoice_item_id']]
            allowed = db.execute('''
                SELECT 1 FROM sorting_rules
                WHERE supplier_product_id = %s AND allowed_product_id = %s
            ''', (supplier_item['supplier_product_id'], item['product_id'])).fetchone()
            
            if not allowed:
                return jsonify({'success': False, 'message': 'الصنف المختار غير مسموح به في قواعد الفرز'})
        
        # إنشاء فاتورة المندوب
        cursor = db.execute('''
            INSERT INTO agent_invoices (supplier_invoice_id, agent_id, status)
            VALUES (%s, %s, 'draft')
        ''', (supplier_invoice_id, session['user_id']))
        agent_invoice_id = cursor.lastrowid
        
        # إضافة بنود الفرز
        for item in parsed_items:
            db.execute('''
                INSERT INTO agent_invoice_items (agent_invoice_id, supplier_invoice_item_id, product_id, quantity)
                VALUES (%s, %s, %s, %s)
            ''', (agent_invoice_id, item['supplier_invoice_item_id'], 
                  item['product_id'], item['quantity']))
            
            # تحديث الكمية المفرزة في فاتورة المورد
            db.execute('''
                UPDATE supplier_invoice_items 
                SET sorted_quantity = sorted_quantity + %s
                WHERE id = %s
            ''', (item['quantity'], item['supplier_invoice_item_id']))
        
        # تحديث حالة فاتورة المورد
        db.execute("UPDATE supplier_invoices SET status = 'sorting' WHERE id = %s", (supplier_invoice_id,))
        
        db.commit()
        return jsonify({'success': True, 'id': agent_invoice_id})
    
    items = db.execute('''
        SELECT sii.*, sp.supplier_product_name, sp.pack_size, p.name as product_name
        FROM supplier_invoice_items sii
        JOIN supplier_products sp ON sp.id = sii.supplier_product_id
        JOIN products p ON p.id = sp.product_id
        WHERE sii.invoice_id = %s
    ''', (supplier_invoice_id,)).fetchall()
    
    # جلب قواعد الفرز لكل صنف
    items_with_rules = []
    for item in items:
        rules = db.execute('''
            SELECT sr.allowed_product_id, p.name as product_name
            FROM sorting_rules sr
            JOIN products p ON p.id = sr.allowed_product_id
            WHERE sr.supplier_product_id = %s
        ''', (item['supplier_product_id'],)).fetchall()
        
        items_with_rules.append({
            **dict(item),
            'allowed_products': [dict(r) for r in rules]
        })
    
    return render_template('sort_invoice.html', invoice=invoice, items=items_with_rules)

@app.route('/api/agent-invoices/<int:id>/submit', methods=['POST'])
@role_required('manager', 'agent')
def submit_agent_invoice(id):
    db = get_db()
    
    agent_invoice = db.execute('''
        SELECT id, supplier_invoice_id, agent_id, status
        FROM agent_invoices
        WHERE id = %s
    ''', (id,)).fetchone()
    
    if not agent_invoice:
        return jsonify({'success': False, 'message': 'فاتورة المندوب غير موجودة'}), 404
    
    if session.get('role') == 'agent' and agent_invoice['agent_id'] != session.get('user_id'):
        return jsonify({'success': False, 'message': 'لا يمكنك تسليم فاتورة ليست تابعة لك'}), 403
    
    if agent_invoice['status'] != 'draft':
        return jsonify({'success': False, 'message': 'لا يمكن تسليم فاتورة ليست في حالة مسودة'})
    
    supplier_invoice = db.execute(
        'SELECT id, status FROM supplier_invoices WHERE id = %s',
        (agent_invoice['supplier_invoice_id'],)
    ).fetchone()
    
    if not supplier_invoice:
        return jsonify({'success': False, 'message': 'فاتورة المورد غير موجودة'}), 404
    
    if supplier_invoice['status'] not in ('pending', 'sorting'):
        return jsonify({'success': False, 'message': 'حالة فاتورة المورد لا تسمح بالتسليم'})
    
    updated_rows = db.execute('''
        UPDATE agent_invoices SET status = 'submitted', submitted_at = %s
        WHERE id = %s AND status = 'draft'
    ''', (datetime.now().isoformat(), id)).rowcount
    
    if updated_rows == 0:
        return jsonify({'success': False, 'message': 'تم تحديث حالة الفاتورة بواسطة مستخدم آخر'})
    
    db.execute("UPDATE supplier_invoices SET status = 'delivered' WHERE id = %s", (agent_invoice['supplier_invoice_id'],))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم تسليم الفاتورة للمخزن'})

# ═══════════════════════════════════════════════════════════════
# استلام المخزن
# ═══════════════════════════════════════════════════════════════

@app.route('/warehouse')
@role_required('manager', 'warehouse')
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
@role_required('manager', 'warehouse')
def receive_invoice(agent_invoice_id):
    db = get_db()
    
    agent_invoice = db.execute('''
        SELECT id, supplier_invoice_id, status
        FROM agent_invoices
        WHERE id = %s
    ''', (agent_invoice_id,)).fetchone()
    
    if not agent_invoice:
        return jsonify({'success': False, 'message': 'فاتورة المندوب غير موجودة'}), 404
    
    if agent_invoice['status'] == 'received':
        return jsonify({'success': False, 'message': 'تم استلام هذه الفاتورة مسبقاً'})
    
    if agent_invoice['status'] != 'submitted':
        return jsonify({'success': False, 'message': 'لا يمكن استلام فاتورة ليست في حالة التسليم'})
    
    supplier_invoice = db.execute(
        'SELECT id, status FROM supplier_invoices WHERE id = %s',
        (agent_invoice['supplier_invoice_id'],)
    ).fetchone()
    
    if not supplier_invoice:
        return jsonify({'success': False, 'message': 'فاتورة المورد غير موجودة'}), 404
    
    if supplier_invoice['status'] != 'delivered':
        return jsonify({'success': False, 'message': 'حالة فاتورة المورد لا تسمح بالاستلام'})
    
    # جلب البنود وتحديث المخزون
    items = db.execute('''
        SELECT aii.product_id, aii.quantity
        FROM agent_invoice_items aii
        WHERE aii.agent_invoice_id = %s
    ''', (agent_invoice_id,)).fetchall()
    
    if not items:
        return jsonify({'success': False, 'message': 'لا توجد بنود للاستلام في هذه الفاتورة'})
    
    # تحديث حالة فاتورة المندوب
    updated_rows = db.execute('''
        UPDATE agent_invoices 
        SET status = 'received', received_at = %s, received_by = %s
        WHERE id = %s AND status = 'submitted'
    ''', (datetime.now().isoformat(), session['user_id'], agent_invoice_id)).rowcount
    
    if updated_rows == 0:
        return jsonify({'success': False, 'message': 'تم تحديث حالة الفاتورة بواسطة مستخدم آخر'})
    
    for item in items:
        # تحديث المخزون
        db.execute('''
            UPDATE products SET current_stock = current_stock + %s
            WHERE id = %s
        ''', (item['quantity'], item['product_id']))
        
        # تسجيل حركة المخزون
        db.execute('''
            INSERT INTO inventory_movements (product_id, movement_type, quantity, reference_type, reference_id, created_by)
            VALUES (%s, 'in', %s, 'agent_invoice', %s, %s)
        ''', (item['product_id'], item['quantity'], agent_invoice_id, session['user_id']))
    
    # تحديث حالة فاتورة المورد
    db.execute("UPDATE supplier_invoices SET status = 'received' WHERE id = %s", (agent_invoice['supplier_invoice_id'],))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم استلام البضاعة وتحديث المخزون'})

# ═══════════════════════════════════════════════════════════════
# المخزون
# ═══════════════════════════════════════════════════════════════

@app.route('/inventory')
@role_required('manager', 'warehouse')
def inventory():
    db = get_db()
    
    products_list = db.execute('''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.is_active = 1
        ORDER BY p.name
    ''').fetchall()
    
    # جلب وحدات كل صنف
    products_with_units = []
    for p in products_list:
        product = dict(p)
        units = db.execute('''
            SELECT pu.*, u.name as unit_name, u.symbol
            FROM product_units pu
            JOIN units u ON u.id = pu.unit_id
            WHERE pu.product_id = %s
            ORDER BY pu.conversion_factor
        ''', (p['id'],)).fetchall()
        product['units'] = [dict(u) for u in units]
        products_with_units.append(product)
    
    # حساب الإحصائيات
    stats = {
        'total': len(products_with_units),
        'above_min': sum(1 for p in products_with_units if p['current_stock'] > p['min_stock']),
        'below_min': sum(1 for p in products_with_units if p['current_stock'] <= p['min_stock'] and p['current_stock'] > 0),
        'zero_stock': sum(1 for p in products_with_units if p['current_stock'] == 0),
    }
    
    return render_template('inventory.html', products=products_with_units, stats=stats)

@app.route('/api/inventory/movements/<int:product_id>')
@role_required('manager', 'warehouse')
def product_movements(product_id):
    db = get_db()
    movements = db.execute('''
        SELECT im.*, u.full_name as created_by_name
        FROM inventory_movements im
        LEFT JOIN users u ON u.id = im.created_by
        WHERE im.product_id = %s
        ORDER BY im.created_at DESC
        LIMIT 50
    ''', (product_id,)).fetchall()
    return jsonify([dict(m) for m in movements])

# ═══════════════════════════════════════════════════════════════
# التقارير
# ═══════════════════════════════════════════════════════════════

@app.route('/reports')
@role_required('manager')
def reports():
    return render_template('reports.html')

@app.route('/api/reports/purchases')
@role_required('manager')
def report_purchases():
    db = get_db()
    start = request.args.get('start', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end = request.args.get('end', datetime.now().strftime('%Y-%m-%d'))
    
    data = db.execute('''
        SELECT s.name as supplier_name, SUM(si.total_amount) as total,
               COUNT(si.id) as invoice_count
        FROM supplier_invoices si
        JOIN suppliers s ON s.id = si.supplier_id
        WHERE si.invoice_date BETWEEN %s AND %s
        GROUP BY s.id
        ORDER BY total DESC
    ''', (start, end)).fetchall()
    
    return jsonify([dict(d) for d in data])

@app.route('/api/reports/supplier-debts')
@role_required('manager')
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
# الإعدادات
# ═══════════════════════════════════════════════════════════════

@app.route('/settings')
@role_required('manager')
def settings():
    db = get_db()
    settings_list = db.execute('SELECT * FROM settings').fetchall()
    settings_dict = {s['key']: s['value'] for s in settings_list}
    return render_template('settings.html', settings=settings_dict)

@app.route('/api/settings', methods=['POST'])
@role_required('manager')
def api_settings():
    db = get_db()
    data = request.json
    
    for key, value in data.items():
        db.execute('UPDATE settings SET value = %s WHERE key = %s', (value, key))
    
    db.commit()
    return jsonify({'success': True, 'message': 'تم حفظ الإعدادات'})

@app.route('/api/backup')
@role_required('manager')
def api_backup():
    import shutil
    from datetime import datetime
    
    db_path = app.config['DATABASE']
    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(os.path.dirname(db_path), 'backups', backup_name)
    
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(db_path, backup_path)
    
    return jsonify({'success': True, 'message': f'تم النسخ الاحتياطي: {backup_name}'})

# ═══════════════════════════════════════════════════════════════
# تشغيل التطبيق
# ═══════════════════════════════════════════════════════════════

def generate_ssl_cert():
    """إنشاء شهادة SSL ذاتية التوقيع"""
    from OpenSSL import crypto
    
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        return cert_file, key_file
    
    # إنشاء مفتاح
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    
    # إنشاء شهادة
    cert = crypto.X509()
    cert.get_subject().C = "YE"
    cert.get_subject().ST = "Sanaa"
    cert.get_subject().L = "Sanaa"
    cert.get_subject().O = "Supermarket"
    cert.get_subject().OU = "IT"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # سنة واحدة
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # حفظ الملفات
    with open(cert_file, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open(key_file, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
    
    return cert_file, key_file

if __name__ == '__main__':
    import sys
    
    with app.app_context():
        init_db()
    
    # التحقق من وضع HTTPS
    use_https = '--https' in sys.argv or os.environ.get('USE_HTTPS', '').lower() == 'true'
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')  # تغيير للسماح بالوصول الخارجي
    port = int(os.environ.get('FLASK_RUN_PORT', '5555'))
    
    print('=' * 50)
    print('Supermarket Management System')
    print('=' * 50)
    
    if use_https:
        cert_file, key_file = generate_ssl_cert()
        print(f'HTTPS Mode')
        print(f'URL: https://localhost:{port}')
        print(f'URL: https://<your-tailscale-ip>:{port}')
    else:
        print(f'URL: http://localhost:{port}')
    
    print('User: admin')
    print('Password: admin')
    print('=' * 50)
    print('For mobile + camera: python app.py --https')
    print('=' * 50)
    
    if use_https:
        app.run(
            debug=False,
            host=host,
            port=port,
            ssl_context=(cert_file, key_file),
            use_reloader=False,
            threaded=True
        )
    else:
        app.run(
            debug=app.config['DEBUG'],
            host=host,
            port=port,
            use_reloader=False,
            threaded=True
        )
