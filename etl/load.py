"""Carga dimensional: DDL via ORM, surrogate keys, SCD Type 2, audit log, reconciliacion."""

from datetime import date, datetime
from decimal import Decimal

import pandas as pd
from sqlalchemy import func, insert, select, text, update

from db.engine import get_engine
from db.models import (
    Base,
    DCustomer,
    DProduct,
    EtlLog,
    FSales,
)

TODAY = date.today()


def _col(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of {candidates} found. Available: {df.columns.tolist()}")


# ── Schema management ────────────────────────────────────────────────


def create_schema(engine) -> None:
    print("Creando schema dimensional ...")
    Base.metadata.create_all(engine)
    print("  Schema creado OK")


def drop_fk_constraints(engine) -> None:
    print("Eliminando FK constraints de f_sales ...")
    with engine.connect() as conn:
        conn.execute(text("""
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT conname
                    FROM pg_constraint
                    WHERE conrelid = 'f_sales'::regclass
                      AND contype = 'f'
                )
                LOOP
                    EXECUTE 'ALTER TABLE f_sales DROP CONSTRAINT ' || quote_ident(r.conname);
                END LOOP;
            END $$;
        """))
        conn.commit()
    print("  FK constraints eliminados")


def create_indexes(engine) -> None:
    print("Creando indices analiticos ...")
    with engine.connect() as conn:
        for idx in [
            "CREATE INDEX IF NOT EXISTS idx_f_sales_date    ON f_sales (order_date_sk)",
            "CREATE INDEX IF NOT EXISTS idx_f_sales_product ON f_sales (product_sk)",
            "CREATE INDEX IF NOT EXISTS idx_f_sales_customer ON f_sales (customer_sk)",
            "CREATE INDEX IF NOT EXISTS idx_f_sales_location ON f_sales (location_sk)",
            "CREATE INDEX IF NOT EXISTS idx_d_customer_id   ON d_customer (customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_d_product_id    ON d_product (product_id)",
        ]:
            conn.execute(text(idx))  # noqa: S608
        conn.commit()
    print("  Indices creados OK")


def enforce_constraints(engine) -> None:
    print("Aplicando PK/FK constraints ...")
    with engine.connect() as conn:
        for c in [
            "ALTER TABLE d_date      ADD PRIMARY KEY (date_sk)",
            "ALTER TABLE d_location  ADD PRIMARY KEY (location_sk)",
            "ALTER TABLE d_order     ADD PRIMARY KEY (order_id)",
            "ALTER TABLE d_segment   ADD PRIMARY KEY (segment_sk)",
        ]:
            try:
                conn.execute(text(c))  # noqa: S608
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"  Warning: {e}")
                conn.rollback()
        for c in [
            "ALTER TABLE f_sales ADD CONSTRAINT fk_sales_date "
            "FOREIGN KEY (order_date_sk) REFERENCES d_date(date_sk)",
            "ALTER TABLE f_sales ADD CONSTRAINT fk_sales_ship "
            "FOREIGN KEY (ship_date_sk) REFERENCES d_date(date_sk)",
            "ALTER TABLE f_sales ADD CONSTRAINT fk_sales_customer "
            "FOREIGN KEY (customer_sk) REFERENCES d_customer(customer_sk)",
            "ALTER TABLE f_sales ADD CONSTRAINT fk_sales_product "
            "FOREIGN KEY (product_sk) REFERENCES d_product(product_sk)",
            "ALTER TABLE f_sales ADD CONSTRAINT fk_sales_location "
            "FOREIGN KEY (location_sk) REFERENCES d_location(location_sk)",
            "ALTER TABLE f_sales ADD CONSTRAINT fk_sales_order "
            "FOREIGN KEY (order_id) REFERENCES d_order(order_id)",
        ]:
            try:
                conn.execute(text(c))  # noqa: S608
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"  Warning: {e}")
                conn.rollback()
    print("  Constraints aplicados OK")


# ── ETL audit log ────────────────────────────────────────────────────


def log_etl(engine, step: str, rows: int, status: str, msg: str, dur: float) -> None:
    with engine.connect() as conn:
        conn.execute(
            insert(EtlLog).values(
                step=step,
                rows_affected=rows,
                status=status,
                message=msg,
                duration_sec=Decimal(str(round(dur, 2))),
            )
        )
        conn.commit()


# ── Surrogate key helpers ───────────────────────────────────────────


def _get_next_sk(engine, table: str, pk_col: str) -> int:
    with engine.connect() as conn:
        result = conn.execute(
            select(func.coalesce(func.max(text(pk_col)), 0) + 1).select_from(  # noqa: S608
                text(table)  # noqa: S608
            )
        )
        return result.scalar()


# ── SCD Type 2 merge helpers ─────────────────────────────────────────


def _expire_scd2(engine, table, pk_col: str, business_key: str, keys_to_expire) -> None:
    """Expire records using Core UPDATE with parameterized IN clause."""
    if not keys_to_expire:
        return
    with engine.connect() as conn:
        stmt = (
            update(table)
            .where(getattr(table, business_key).in_(list(keys_to_expire)))
            .where(table.current_flag == "Y")
            .values(current_flag="N", expiration_date=TODAY)
        )
        conn.execute(stmt)
        conn.commit()


def _scd2_merge(engine, table, pk_col: str, new_df: pd.DataFrame,
                business_key: str, tracked_cols: list[str]) -> pd.DataFrame:
    """SCD Type 2 merge: expire changed, insert new, keep unchanged."""
    try:
        existing = pd.read_sql(
            select(table).where(table.current_flag == "Y"),
            engine,
        )
    except Exception:
        existing = pd.DataFrame(columns=[business_key])

    existing_keys = set(existing[business_key].values) if business_key in existing.columns else set()
    new_keys = set(new_df[business_key].values)

    changed_mask = pd.Series(False, index=new_df.index)
    for _, old_row in existing[existing[business_key].isin(new_keys)].iterrows():
        new_row = new_df[new_df[business_key] == old_row[business_key]].iloc[0]
        if any(new_row[col] != old_row[col] for col in tracked_cols if col in new_df.columns):
            changed_mask.iloc[new_df[new_df[business_key] == old_row[business_key]].index[0]] = True

    keys_to_expire = existing_keys - new_keys | set(new_df[changed_mask][business_key].values)
    _expire_scd2(engine, table, pk_col, business_key, keys_to_expire)

    next_sk = _get_next_sk(engine, table.__tablename__, pk_col)
    rows_to_insert = []
    for _, row in new_df.iterrows():
        if row[business_key] not in existing_keys or row[business_key] in new_df[changed_mask][business_key].values:
            rows_to_insert.append(row.to_dict())

    if rows_to_insert:
        insert_df = pd.DataFrame(rows_to_insert)
        insert_df[pk_col] = range(next_sk, next_sk + len(insert_df))
        insert_df["effective_date"] = TODAY
        insert_df["expiration_date"] = None
        insert_df["current_flag"] = "Y"
        insert_df.to_sql(table.__tablename__, engine, if_exists="append", index=False)

    return new_df


# ── Dimension builders ────────────────────────────────────────────────


def _build_d_date(df, engine) -> pd.DataFrame:
    t0 = datetime.now()
    order_col = _col(df, "order_date", "Order Date")
    ship_col = _col(df, "ship_date", "Ship Date")
    dates = pd.to_datetime(pd.concat([df[order_col], df[ship_col]]).dropna().unique())
    dates = pd.Series(sorted(dates)).dt.floor("D")
    dates = dates.drop_duplicates().reset_index(drop=True)
    d = pd.DataFrame({
        "date_sk": range(1, len(dates) + 1),
        "date": dates,
        "day": dates.dt.day,
        "month": dates.dt.month,
        "month_name": dates.dt.month_name(),
        "quarter": dates.dt.quarter,
        "year": dates.dt.year,
        "week_day": dates.dt.day_name(),
        "is_weekend": dates.dt.dayofweek >= 5,
    })
    d.to_sql("d_date", engine, if_exists="replace", index=False)
    log_etl(engine, "d_date", len(d), "OK", "Dimension fecha", (datetime.now() - t0).total_seconds())
    print(f"  D_Date: {len(d)} filas")
    return d


def _build_d_customer(df, engine) -> pd.DataFrame:
    t0 = datetime.now()
    cust_id_col = _col(df, "customer_id", "Customer ID")
    cust_name_col = _col(df, "customer_name", "Customer Name")
    seg_col = _col(df, "segment", "Segment")
    customers = df[[cust_id_col, cust_name_col, seg_col]].drop_duplicates(cust_id_col)
    new_d = pd.DataFrame({
        "customer_id": customers[cust_id_col].values,
        "customer_name": customers[cust_name_col].values,
        "segment": customers[seg_col].values,
    })

    try:
        existing = pd.read_sql(
            select(DCustomer.customer_sk, DCustomer.customer_id,
                   DCustomer.customer_name, DCustomer.segment)
            .where(DCustomer.current_flag == "Y"),
            engine,
        )
    except Exception:
        existing = pd.DataFrame()

    if len(existing) > 0:
        existing_map = existing.set_index("customer_id")[["customer_name", "segment"]].to_dict("index")
        changed = []
        for _, row in new_d.iterrows():
            cid = row["customer_id"]
            if cid in existing_map:
                old = existing_map[cid]
                if row["customer_name"] != old["customer_name"] or row["segment"] != old["segment"]:
                    changed.append(cid)
            else:
                changed.append(cid)

        _expire_scd2(engine, DCustomer, "customer_sk", "customer_id", changed)

        next_sk = _get_next_sk(engine, "d_customer", "customer_sk")
        to_insert = new_d[new_d["customer_id"].isin(changed)].copy()
        if len(to_insert) > 0:
            to_insert["customer_sk"] = range(next_sk, next_sk + len(to_insert))
            to_insert["effective_date"] = TODAY
            to_insert["expiration_date"] = None
            to_insert["current_flag"] = "Y"
            to_insert.to_sql("d_customer", engine, if_exists="append", index=False)

        d = pd.read_sql(select(DCustomer).where(DCustomer.current_flag == "Y"), engine)
    else:
        d = pd.DataFrame({
            "customer_sk": range(1, len(new_d) + 1),
            "customer_id": new_d["customer_id"].values,
            "customer_name": new_d["customer_name"].values,
            "segment": new_d["segment"].values,
            "effective_date": [TODAY] * len(new_d),
            "expiration_date": [None] * len(new_d),
            "current_flag": ["Y"] * len(new_d),
        })
        d.to_sql("d_customer", engine, if_exists="replace", index=False)

    log_etl(engine, "d_customer", len(d), "OK", "Dimension cliente SCD2", (datetime.now() - t0).total_seconds())
    print(f"  D_Customer: {len(d)} filas (SCD Type 2)")
    return d


def _build_d_product(df, engine) -> pd.DataFrame:
    t0 = datetime.now()
    prod_id_col = _col(df, "product_id", "Product ID")
    prod_name_col = _col(df, "product_name", "Product Name")
    cat_col = _col(df, "category", "Category")
    subcat_col = _col(df, "sub_category", "Sub-Category")
    products = df[[prod_id_col, prod_name_col, cat_col, subcat_col]].drop_duplicates(prod_id_col)
    new_d = pd.DataFrame({
        "product_id": products[prod_id_col].values,
        "product_name": products[prod_name_col].values,
        "category": products[cat_col].values,
        "sub_category": products[subcat_col].values,
    })

    try:
        existing = pd.read_sql(
            select(DProduct.product_sk, DProduct.product_id,
                   DProduct.product_name, DProduct.category, DProduct.sub_category)
            .where(DProduct.current_flag == "Y"),
            engine,
        )
    except Exception:
        existing = pd.DataFrame()

    if len(existing) > 0:
        existing_map = existing.set_index("product_id")[["product_name", "category", "sub_category"]].to_dict("index")
        changed = []
        for _, row in new_d.iterrows():
            pid = row["product_id"]
            if pid in existing_map:
                old = existing_map[pid]
                if any(row[c] != old[c] for c in ["product_name", "category", "sub_category"]):
                    changed.append(pid)
            else:
                changed.append(pid)

        _expire_scd2(engine, DProduct, "product_sk", "product_id", changed)

        next_sk = _get_next_sk(engine, "d_product", "product_sk")
        to_insert = new_d[new_d["product_id"].isin(changed)].copy()
        if len(to_insert) > 0:
            to_insert["product_sk"] = range(next_sk, next_sk + len(to_insert))
            to_insert["effective_date"] = TODAY
            to_insert["expiration_date"] = None
            to_insert["current_flag"] = "Y"
            to_insert.to_sql("d_product", engine, if_exists="append", index=False)

        d = pd.read_sql(select(DProduct).where(DProduct.current_flag == "Y"), engine)
    else:
        d = pd.DataFrame({
            "product_sk": range(1, len(new_d) + 1),
            "product_id": new_d["product_id"].values,
            "product_name": new_d["product_name"].values,
            "category": new_d["category"].values,
            "sub_category": new_d["sub_category"].values,
            "effective_date": [TODAY] * len(new_d),
            "expiration_date": [None] * len(new_d),
            "current_flag": ["Y"] * len(new_d),
        })
        d.to_sql("d_product", engine, if_exists="replace", index=False)

    log_etl(engine, "d_product", len(d), "OK", "Dimension producto SCD2", (datetime.now() - t0).total_seconds())
    print(f"  D_Product: {len(d)} filas (SCD Type 2)")
    return d


def _build_d_location(df, engine) -> pd.DataFrame:
    t0 = datetime.now()
    country_col = _col(df, "country", "Country")
    region_col = _col(df, "region", "Region")
    state_col = _col(df, "state", "State")
    city_col = _col(df, "city", "City")
    postal_col = _col(df, "postal_code", "Postal Code")
    locations = df[[country_col, region_col, state_col, city_col, postal_col]].drop_duplicates()
    d = pd.DataFrame({
        "location_sk": range(1, len(locations) + 1),
        "country": locations[country_col].values,
        "region": locations[region_col].values,
        "state": locations[state_col].values,
        "city": locations[city_col].values,
        "postal_code": locations[postal_col].values,
    })
    d.to_sql("d_location", engine, if_exists="replace", index=False)
    log_etl(engine, "d_location", len(d), "OK", "Dimension ubicacion", (datetime.now() - t0).total_seconds())
    print(f"  D_Location: {len(d)} filas")
    return d


def _build_d_order(df, engine) -> pd.DataFrame:
    t0 = datetime.now()
    order_id_col = _col(df, "order_id", "Order ID")
    ship_mode_col = _col(df, "ship_mode", "Ship Mode")
    orders = df[[order_id_col, ship_mode_col]].drop_duplicates(order_id_col)
    d = pd.DataFrame({
        "order_id": orders[order_id_col].values,
        "ship_mode": orders[ship_mode_col].values,
    })
    d.to_sql("d_order", engine, if_exists="replace", index=False)
    log_etl(engine, "d_order", len(d), "OK", "Dimension orden degenerada", (datetime.now() - t0).total_seconds())
    print(f"  D_Order: {len(d)} filas (degenerada)")
    return d


def _build_d_segment(df, engine) -> pd.DataFrame:
    t0 = datetime.now()
    seg_col = _col(df, "segment", "Segment")
    segments = sorted(df[seg_col].dropna().unique())
    d = pd.DataFrame({
        "segment_sk": range(1, len(segments) + 1),
        "segment_name": segments,
    })
    d.to_sql("d_segment", engine, if_exists="replace", index=False)
    log_etl(engine, "d_segment", len(d), "OK", "Dimension segmento", (datetime.now() - t0).total_seconds())
    print(f"  D_Segment: {len(d)} filas")
    return d


# ── Fact table (vectorized) ──────────────────────────────────────────


def _build_f_sales(df, dims, engine) -> None:
    t0 = datetime.now()
    cols = dims["_cols"]

    date_map = dict(zip(dims["date"]["date"].dt.strftime("%Y-%m-%d"), dims["date"]["date_sk"]))
    cust_map = dict(zip(dims["customer"]["customer_id"], dims["customer"]["customer_sk"]))
    prod_map = dict(zip(dims["product"]["product_id"], dims["product"]["product_sk"]))
    loc_lookup = {(r["city"], r["state"]): int(r["location_sk"]) for _, r in dims["location"].iterrows()}

    order_col = cols["order"]
    ship_col = cols["ship"]
    cust_id_col = cols["cust_id"]
    prod_id_col = cols["prod_id"]
    city_col = cols["city"]
    state_col = cols["state"]
    order_id_col = _col(df, "order_id", "Order ID")
    ship_mode_col = _col(df, "ship_mode", "Ship Mode")
    sales_col = _col(df, "sales", "Sales")
    qty_col = _col(df, "quantity", "Quantity")
    disc_col = _col(df, "discount", "Discount")
    profit_col = _col(df, "profit", "Profit")

    f = pd.DataFrame()
    f["order_date_sk"] = pd.to_datetime(df[order_col]).dt.strftime("%Y-%m-%d").map(date_map).fillna(1).astype(int)
    f["ship_date_sk"] = pd.to_datetime(df[ship_col]).dt.strftime("%Y-%m-%d").map(date_map).fillna(1).astype(int)
    f["customer_sk"] = df[cust_id_col].map(cust_map).fillna(1).astype(int)
    f["product_sk"] = df[prod_id_col].map(prod_map).fillna(1).astype(int)
    f["location_sk"] = df.apply(lambda r: loc_lookup.get((r[city_col], r[state_col]), 1), axis=1).astype(int)
    f["order_id"] = df[order_id_col].values
    f["ship_mode"] = df[ship_mode_col].values
    f["sales"] = df[sales_col].values
    f["quantity"] = df[qty_col].values
    f["discount"] = df[disc_col].values
    f["profit"] = df[profit_col].values

    f.to_sql("f_sales", engine, if_exists="replace", index=False)
    dur = (datetime.now() - t0).total_seconds()
    log_etl(engine, "f_sales", len(f), "OK", "Hecho ventas", dur)
    print(f"  F_Sales: {len(f)} filas cargadas ({dur:.1f}s)")


# ── Reconciliation ───────────────────────────────────────────────────


def reconcile(engine, source_count: int) -> None:
    t0 = datetime.now()
    with engine.connect() as conn:
        fact_count = conn.execute(select(func.count()).select_from(FSales)).scalar()
        raw_count = conn.execute(
            select(func.count()).select_from(text("raw.superstore_clean"))  # noqa: S608
        ).scalar()

    mismatches = []
    if fact_count != source_count:
        mismatches.append(f"f_sales={fact_count} vs source={source_count}")
    if raw_count != source_count:
        mismatches.append(f"raw={raw_count} vs source={source_count}")

    if mismatches:
        msg = f"DISCREPANCIA: {'; '.join(mismatches)}"
        log_etl(engine, "RECONCILE", fact_count, "WARN", msg, (datetime.now() - t0).total_seconds())
        print(f"  WARNING: {msg}")
    else:
        msg = f"OK: f_sales={fact_count}, raw={raw_count}, source={source_count}"
        log_etl(engine, "RECONCILE", fact_count, "OK", msg, (datetime.now() - t0).total_seconds())
        print(f"  Reconciliacion: {msg}")


# ── Aggregate table for performance (Kimball aggregate fact) ───────────


def create_agg_sales_monthly(engine) -> None:
    t0 = datetime.now()
    with engine.connect() as conn:
        conn.execute(text("""
            DROP MATERIALIZED VIEW IF EXISTS agg_sales_monthly CASCADE
        """))  # noqa: S608
        conn.execute(text("""
            CREATE MATERIALIZED VIEW agg_sales_monthly AS
            SELECT
                dd.year,
                dd.month,
                dd.month_name,
                dd.quarter,
                dl.region,
                dp.category,
                COUNT(DISTINCT f.order_id) AS total_orders,
                SUM(f.sales) AS total_sales,
                SUM(f.profit) AS total_profit,
                SUM(f.quantity) AS total_quantity,
                COUNT(*) AS transaction_count,
                AVG(f.discount) AS avg_discount
            FROM f_sales f
            JOIN d_date dd ON f.order_date_sk = dd.date_sk
            JOIN d_location dl ON f.location_sk = dl.location_sk
            JOIN d_product dp ON f.product_sk = dp.product_sk
            GROUP BY dd.year, dd.month, dd.month_name, dd.quarter, dl.region, dp.category
            ORDER BY dd.year, dd.month, dl.region, dp.category
        """))  # noqa: S608
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_agg_sales_monthly_pk
            ON agg_sales_monthly (year, month, region, category)
        """))  # noqa: S608
        conn.commit()
    log_etl(engine, "AGG_SALES_MONTHLY", 0, "OK",
            "Aggregate table created", (datetime.now() - t0).total_seconds())
    print(f"  Agg_Sales_Monthly: materialized view created ({(datetime.now() - t0).total_seconds():.1f}s)")


# ── Main ─────────────────────────────────────────────────────────────


def load_dimensions(df: pd.DataFrame, engine) -> dict:
    print("Generando dimensiones ...")

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS f_sales CASCADE"))
        conn.commit()

    create_schema(engine)
    drop_fk_constraints(engine)

    d_date = _build_d_date(df, engine)
    d_customer = _build_d_customer(df, engine)
    d_product = _build_d_product(df, engine)
    d_location = _build_d_location(df, engine)
    d_order = _build_d_order(df, engine)
    d_segment = _build_d_segment(df, engine)

    return {
        "date": d_date,
        "customer": d_customer,
        "product": d_product,
        "location": d_location,
        "order": d_order,
        "segment": d_segment,
        "_cols": {
            "order": _col(df, "order_date", "Order Date"),
            "ship": _col(df, "ship_date", "Ship Date"),
            "cust_id": _col(df, "customer_id", "Customer ID"),
            "cust_name": _col(df, "customer_name", "Customer Name"),
            "segment": _col(df, "segment", "Segment"),
            "country": _col(df, "country", "Country"),
            "region": _col(df, "region", "Region"),
            "state": _col(df, "state", "State"),
            "city": _col(df, "city", "City"),
            "postal": _col(df, "postal_code", "Postal Code"),
            "prod_id": _col(df, "product_id", "Product ID"),
            "prod_name": _col(df, "product_name", "Product Name"),
            "category": _col(df, "category", "Category"),
            "subcat": _col(df, "sub_category", "Sub-Category"),
        },
    }


def main():
    t_total = datetime.now()
    engine = get_engine()
    df = pd.read_sql(text("SELECT * FROM raw.superstore_clean"), engine)  # noqa: S608
    source_count = len(df)
    dims = load_dimensions(df, engine)
    _build_f_sales(df, dims, engine)
    create_indexes(engine)
    enforce_constraints(engine)
    create_agg_sales_monthly(engine)
    reconcile(engine, source_count)
    dur_total = (datetime.now() - t_total).total_seconds()
    log_etl(engine, "ETL_TOTAL", source_count, "OK", "Pipeline completo", dur_total)
    print(f"Carga dimensional completada OK ({dur_total:.1f}s total)")


if __name__ == "__main__":
    main()
