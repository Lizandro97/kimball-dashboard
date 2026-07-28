"""Shared utilities for the Superstore BI dashboard."""

from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import Float, select

from db.engine import get_engine
from db.models import DCustomer, DDate, DLocation, DOrder, DProduct, FSales

# ── Color palette (used by chart_service.py) ──────────────────────────
BLUE = "#2563eb"
TEAL = "#0d9488"
AMBER = "#d97706"
ROSE = "#e11d48"
GREEN = "#059669"
RED = "#dc2626"
PURPLE = "#7c3aed"
GRAY = "#94a3b8"
SLATE = "#64748b"

CAT_COLORS = {"Technology": BLUE, "Office Supplies": TEAL, "Furniture": AMBER}
REGION_COLORS = {"West": BLUE, "East": PURPLE, "Central": AMBER, "South": ROSE}
SEGMENT_COLORS = {"Consumer": BLUE, "Corporate": TEAL, "Home Office": PURPLE}


# ── Data loading (SQLAlchemy Core) ──────────────────────────────────

dd_date = DDate.__table__
ds_date = DDate.__table__.alias("ds")
dc = DCustomer.__table__
dp = DProduct.__table__
dl = DLocation.__table__
do_ = DOrder.__table__
f = FSales.__table__

_DIM_QUERY = (
    select(
        f.c.order_id,
        dd_date.c.date.label("order_date"),
        ds_date.c.date.label("ship_date"),
        f.c.sales.cast(Float).label("sales"),
        f.c.quantity.label("quantity"),
        f.c.discount.cast(Float).label("discount"),
        f.c.profit.cast(Float).label("profit"),
        dc.c.customer_name,
        dc.c.segment,
        dp.c.product_name,
        dp.c.category,
        dp.c.sub_category,
        dl.c.country,
        dl.c.region,
        dl.c.state,
        dl.c.city,
        do_.c.ship_mode,
    )
    .select_from(
        f.join(dd_date, f.c.order_date_sk == dd_date.c.date_sk)
        .join(ds_date, f.c.ship_date_sk == ds_date.c.date_sk)
        .join(dc, f.c.customer_sk == dc.c.customer_sk)
        .join(dp, f.c.product_sk == dp.c.product_sk)
        .join(dl, f.c.location_sk == dl.c.location_sk)
        .join(do_, f.c.order_id == do_.c.order_id)
    )
)


def load_data() -> pd.DataFrame:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            df = pd.read_sql(_DIM_QUERY, conn)
        for col in ["order_date", "ship_date"]:
            df[col] = pd.to_datetime(df[col])
        return df
    except Exception:
        return _sample_df()


def filter_data(df: pd.DataFrame, region: str, year: str, segment: str) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if region and region != "Todas":
        mask &= df["region"] == region
    if year and year != "Todos":
        mask &= df["order_date"].dt.year == int(year)
    if segment and segment != "Todos":
        mask &= df["segment"] == segment
    return df[mask].copy()


def fmt_dollar(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"


# ── Sample data generator (fallback when DB unavailable) ──────────────

def _sample_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2014-01-01", "2017-12-31", freq="D")
    n = 9994
    categories = ["Furniture", "Office Supplies", "Technology"]
    regions = ["Central", "East", "South", "West"]
    segments = ["Consumer", "Corporate", "Home Office"]
    sub_cats = {
        "Furniture": ["Bookcases", "Chairs", "Furnishings", "Tables"],
        "Office Supplies": ["Appliances", "Art", "Binders", "Envelopes",
                            "Fasteners", "Labels", "Paper", "Storage", "Supplies"],
        "Technology": ["Accessories", "Copiers", "Machines", "Phones"],
    }
    rows: list[dict[str, Any]] = []
    for i in range(n):
        cat = rng.choice(categories, p=[0.3, 0.4, 0.3])
        sub = rng.choice(sub_cats[cat])
        region = rng.choice(regions, p=[0.25, 0.28, 0.22, 0.25])
        segment = rng.choice(segments, p=[0.5, 0.3, 0.2])
        base_price = rng.uniform(10, 500)
        qty = rng.integers(1, 7)
        discount = rng.choice(
            [0, 0, 0, 0.1, 0.15, 0.2, 0.3, 0.45, 0.6, 0.8],
            p=[0.4, 0, 0, 0.2, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05],
        )
        sales = base_price * qty * (1 - discount)
        profit = sales * rng.uniform(-0.2, 0.4)
        date = rng.choice(dates)
        f"CG-{rng.integers(10000, 99999)}"
        customer_name = rng.choice(["Cliente A", "Cliente B", "Cliente C"])
        f"FUR-{rng.integers(10000000, 99999999)}"
        product_name = rng.choice(["Producto X", "Producto Y", "Producto Z"])
        rows.append({
            "order_id": f"ORD-{i:05d}",
            "order_date": date,
            "ship_date": date + pd.Timedelta(days=rng.integers(1, 7)),
            "sales": round(sales, 2),
            "quantity": qty,
            "discount": discount,
            "profit": round(profit, 2),
            "customer_name": customer_name,
            "segment": segment,
            "product_name": product_name,
            "category": cat,
            "sub_category": sub,
            "country": "United States",
            "region": region,
            "state": rng.choice(["California", "Texas", "New York"]),
            "city": rng.choice(["Los Angeles", "Houston", "NYC"]),
            "ship_mode": rng.choice(["First Class", "Second Class", "Standard Class"]),
        })
    return pd.DataFrame(rows)
