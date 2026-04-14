CREATE TABLE IF NOT EXISTS stocktake_sessions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'open',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

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
