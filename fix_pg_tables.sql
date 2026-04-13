-- Add missing columns
ALTER TABLE categories ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES categories(id);
ALTER TABLE categories ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;

ALTER TABLE agent_invoices ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add missing column to supplier_prices  
ALTER TABLE supplier_prices ADD COLUMN IF NOT EXISTS unit_price DECIMAL(12,2);
UPDATE supplier_prices SET unit_price = price WHERE unit_price IS NULL;

-- Create missing tables
CREATE TABLE IF NOT EXISTS product_units (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    unit_name VARCHAR(100),
    conversion_factor DECIMAL(12,4) DEFAULT 1,
    barcode VARCHAR(100),
    cost_price DECIMAL(12,2),
    sell_price DECIMAL(12,2),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS price_lists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_list_items (
    id SERIAL PRIMARY KEY,
    price_list_id INTEGER REFERENCES price_lists(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    price DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_batches (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    batch_number VARCHAR(100),
    quantity DECIMAL(12,2),
    cost_price DECIMAL(12,2),
    sell_price DECIMAL(12,2),
    manufacture_date DATE,
    expiry_date DATE,
    supplier_id INTEGER REFERENCES suppliers(id),
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
