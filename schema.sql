-- Categories
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Units
CREATE TABLE IF NOT EXISTS units (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE,
    name VARCHAR(500) NOT NULL,
    brand VARCHAR(255),
    barcode VARCHAR(100),
    category_id INTEGER REFERENCES categories(id),
    unit VARCHAR(50) DEFAULT 'piece',
    cost_price DECIMAL(12,2) DEFAULT 0,
    sell_price DECIMAL(12,2) DEFAULT 0,
    min_stock DECIMAL(12,2) DEFAULT 0,
    current_stock DECIMAL(12,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product Barcodes (multiple barcodes per product/unit)
CREATE TABLE IF NOT EXISTS product_barcodes (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    barcode VARCHAR(100) NOT NULL,
    unit VARCHAR(50) DEFAULT 'piece',
    pack_size INTEGER DEFAULT 1,
    cost_price DECIMAL(12,2) DEFAULT 0,
    sell_price DECIMAL(12,2) DEFAULT 0,
    UNIQUE(barcode)
);

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier Products (linking supplier items to our products)
CREATE TABLE IF NOT EXISTS supplier_products (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id),
    supplier_item_name VARCHAR(500),
    supplier_barcode VARCHAR(100),
    product_id INTEGER REFERENCES products(id),
    last_cost DECIMAL(12,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'employee',
    must_change_password BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier Invoices
CREATE TABLE IF NOT EXISTS supplier_invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(100),
    supplier_id INTEGER REFERENCES suppliers(id),
    invoice_date DATE,
    total_amount DECIMAL(14,2) DEFAULT 0,
    paid_amount DECIMAL(14,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier Invoice Items
CREATE TABLE IF NOT EXISTS supplier_invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES supplier_invoices(id) ON DELETE CASCADE,
    supplier_item_name VARCHAR(500),
    supplier_barcode VARCHAR(100),
    quantity DECIMAL(12,2),
    unit_price DECIMAL(12,2),
    total_price DECIMAL(14,2),
    product_id INTEGER REFERENCES products(id),
    sorted_quantity DECIMAL(12,2) DEFAULT 0
);

-- Inventory Movements
CREATE TABLE IF NOT EXISTS inventory_movements (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    movement_type VARCHAR(50),
    quantity DECIMAL(12,2),
    reference_type VARCHAR(50),
    reference_id INTEGER,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pricing History
CREATE TABLE IF NOT EXISTS pricing_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    old_cost DECIMAL(12,2),
    new_cost DECIMAL(12,2),
    old_sell DECIMAL(12,2),
    new_sell DECIMAL(12,2),
    changed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Competitors
CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

-- Competitor Prices
CREATE TABLE IF NOT EXISTS competitor_prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    competitor_id INTEGER REFERENCES competitors(id),
    price DECIMAL(12,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    position VARCHAR(100),
    salary DECIMAL(12,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Batches (for expiry tracking)
CREATE TABLE IF NOT EXISTS batches (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    batch_number VARCHAR(100),
    quantity DECIMAL(12,2),
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_product_barcodes_barcode ON product_barcodes(barcode);
CREATE INDEX IF NOT EXISTS idx_product_barcodes_product ON product_barcodes(product_id);
CREATE INDEX IF NOT EXISTS idx_supplier_products_supplier ON supplier_products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_products_product ON supplier_products(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_product ON inventory_movements(product_id);

-- Stocktaking sessions
CREATE TABLE IF NOT EXISTS stocktake_sessions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'open',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

-- Stocktaking scanned items
CREATE TABLE IF NOT EXISTS stocktake_items (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES stocktake_sessions(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    barcode VARCHAR(100),
    product_name VARCHAR(500),
    unit VARCHAR(50),
    expected_stock DECIMAL(12,2) DEFAULT 0,
    counted_stock DECIMAL(12,2) DEFAULT 1,
    scan_count INTEGER DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Requests for unknown products during stocktake
CREATE TABLE IF NOT EXISTS stocktake_product_requests (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES stocktake_sessions(id) ON DELETE SET NULL,
    barcode VARCHAR(100) NOT NULL,
    product_name VARCHAR(500),
    category_id INTEGER REFERENCES categories(id),
    unit VARCHAR(50),
    notes TEXT,
    image_path TEXT,
    attachment_path TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    requested_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_stocktake_items_session ON stocktake_items(session_id);
CREATE INDEX IF NOT EXISTS idx_stocktake_items_product ON stocktake_items(product_id);
CREATE INDEX IF NOT EXISTS idx_stocktake_requests_status ON stocktake_product_requests(status);
CREATE INDEX IF NOT EXISTS idx_stocktake_requests_barcode ON stocktake_product_requests(barcode);
