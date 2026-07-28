-- D_Date: Dimensión de fechas (SCD Type 0, sin cambios)
CREATE TABLE IF NOT EXISTS d_date (
    date_sk         INTEGER PRIMARY KEY,
    date            DATE NOT NULL,
    day             INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      VARCHAR(20),
    quarter         INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    week_day        VARCHAR(20),
    is_weekend      BOOLEAN DEFAULT FALSE
);

-- D_Customer: Cliente (SCD Type 2, preserva historia)
CREATE TABLE IF NOT EXISTS d_customer (
    customer_sk      INTEGER PRIMARY KEY,
    customer_id      VARCHAR(50),
    customer_name    VARCHAR(100),
    segment          VARCHAR(50),
    effective_date   DATE NOT NULL,
    expiration_date  DATE,
    current_flag     CHAR(1) DEFAULT 'Y'
);

-- D_Product: Producto (SCD Type 2, preserva historia)
CREATE TABLE IF NOT EXISTS d_product (
    product_sk       INTEGER PRIMARY KEY,
    product_id       VARCHAR(50),
    product_name     VARCHAR(200),
    category         VARCHAR(50),
    sub_category     VARCHAR(50),
    effective_date   DATE NOT NULL,
    expiration_date  DATE,
    current_flag     CHAR(1) DEFAULT 'Y'
);

-- D_Location: Ubicación (SCD Type 1, sobrescritura)
CREATE TABLE IF NOT EXISTS d_location (
    location_sk     INTEGER PRIMARY KEY,
    country         VARCHAR(50),
    region          VARCHAR(50),
    state           VARCHAR(50),
    city            VARCHAR(100),
    postal_code     VARCHAR(20)
);

-- D_Order: Orden degenerada
CREATE TABLE IF NOT EXISTS d_order (
    order_id        VARCHAR(50) PRIMARY KEY,
    ship_mode       VARCHAR(50)
);

-- D_Segment: Segmento de mercado (SCD Type 1)
CREATE TABLE IF NOT EXISTS d_segment (
    segment_sk      INTEGER PRIMARY KEY,
    segment_name    VARCHAR(50) UNIQUE
);

-- F_Sales: Fact table transaccional
CREATE TABLE IF NOT EXISTS f_sales (
    order_date_sk  INTEGER NOT NULL REFERENCES d_date(date_sk),
    ship_date_sk   INTEGER NOT NULL REFERENCES d_date(date_sk),
    customer_sk    INTEGER NOT NULL REFERENCES d_customer(customer_sk),
    product_sk     INTEGER NOT NULL REFERENCES d_product(product_sk),
    location_sk    INTEGER NOT NULL REFERENCES d_location(location_sk),
    order_id       VARCHAR(50),
    ship_mode      VARCHAR(50),
    sales          NUMERIC(12,4),
    quantity       INTEGER,
    discount       NUMERIC(5,4),
    profit         NUMERIC(12,4),
    PRIMARY KEY (order_date_sk, customer_sk, product_sk, location_sk)
);

-- Índices para consultas analíticas
CREATE INDEX IF NOT EXISTS idx_f_sales_date    ON f_sales (order_date_sk);
CREATE INDEX IF NOT EXISTS idx_f_sales_product ON f_sales (product_sk);
CREATE INDEX IF NOT EXISTS idx_f_sales_customer ON f_sales (customer_sk);
