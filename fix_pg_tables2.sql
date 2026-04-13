-- Fix product_units: add unit_id column
ALTER TABLE product_units ADD COLUMN IF NOT EXISTS unit_id INTEGER;

-- Fix agent_invoices: add received_by column
ALTER TABLE agent_invoices ADD COLUMN IF NOT EXISTS received_by INTEGER REFERENCES users(id);

-- Fix product_batches: add supplier_invoice_id column
ALTER TABLE product_batches ADD COLUMN IF NOT EXISTS supplier_invoice_id INTEGER REFERENCES supplier_invoices(id);

-- Create product_prices table
CREATE TABLE IF NOT EXISTS product_prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    price_list_id INTEGER REFERENCES price_lists(id),
    price DECIMAL(12,2),
    min_qty DECIMAL(12,2) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
