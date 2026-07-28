-- Q1: Ventas y utilidad por región y categoría
SELECT
    l.region,
    p.category,
    SUM(f.sales) AS total_sales,
    SUM(f.profit) AS total_profit,
    COUNT(DISTINCT f.order_id) AS order_count
FROM f_sales f
JOIN d_location l ON f.location_sk = l.location_sk
JOIN d_product p ON f.product_sk = p.product_sk
GROUP BY l.region, p.category
ORDER BY total_sales DESC;

-- Q2: Top 10 productos más rentables
SELECT
    p.product_name,
    p.sub_category,
    SUM(f.sales) AS total_sales,
    SUM(f.profit) AS total_profit,
    (SUM(f.profit) / NULLIF(SUM(f.sales), 0)) * 100 AS margin_pct
FROM f_sales f
JOIN d_product p ON f.product_sk = p.product_sk
GROUP BY p.product_name, p.sub_category
ORDER BY total_profit DESC
LIMIT 10;

-- Q5: Impacto del descuento en rentabilidad
SELECT
    CASE
        WHEN f.discount = 0 THEN 'Sin descuento'
        WHEN f.discount <= 0.2 THEN 'Bajo (<=20%)'
        WHEN f.discount <= 0.5 THEN 'Medio (<=50%)'
        ELSE 'Alto (>50%)'
    END AS discount_tier,
    COUNT(*) AS transactions,
    SUM(f.sales) AS total_sales,
    SUM(f.profit) AS total_profit,
    AVG(f.discount) AS avg_discount
FROM f_sales f
GROUP BY discount_tier
ORDER BY avg_discount;
