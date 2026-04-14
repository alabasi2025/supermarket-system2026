ALTER TABLE stocktake_items ADD COLUMN IF NOT EXISTS selected_unit VARCHAR(50);
ALTER TABLE stocktake_items ADD COLUMN IF NOT EXISTS pack_size INTEGER DEFAULT 1;
ALTER TABLE stocktake_items ADD COLUMN IF NOT EXISTS production_date DATE;
ALTER TABLE stocktake_items ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE stocktake_items ADD COLUMN IF NOT EXISTS batch_no VARCHAR(100);
ALTER TABLE stocktake_items ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE stocktake_items ADD COLUMN IF NOT EXISTS image_path TEXT;
ALTER TABLE stocktake_items ADD COLUMN IF NOT EXISTS attachment_path TEXT;

ALTER TABLE stocktake_product_requests ADD COLUMN IF NOT EXISTS pack_size INTEGER DEFAULT 1;
ALTER TABLE stocktake_product_requests ADD COLUMN IF NOT EXISTS quantity_counted DECIMAL(12,2) DEFAULT 1;
ALTER TABLE stocktake_product_requests ADD COLUMN IF NOT EXISTS production_date DATE;
ALTER TABLE stocktake_product_requests ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE stocktake_product_requests ADD COLUMN IF NOT EXISTS batch_no VARCHAR(100);
ALTER TABLE stocktake_product_requests ADD COLUMN IF NOT EXISTS cost_price DECIMAL(12,2);
ALTER TABLE stocktake_product_requests ADD COLUMN IF NOT EXISTS sell_price DECIMAL(12,2);
