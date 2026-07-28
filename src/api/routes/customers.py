"""GET /api/customers — Clientes."""

from fastapi import APIRouter, Query

from api.services.chart_service import (
    build_customer_frequency,
    build_segment_distribution,
    build_segment_margin,
    filter_data,
    fmt_dollar,
    load_data,
)

router = APIRouter()


@router.get("/customers")
def get_customers(
    region: str = Query("Todas"),
    year: str = Query("Todos"),
    segment: str = Query("Todos"),
    theme: str = Query("light"),
):
    df_global = load_data()
    df = filter_data(df_global, region, year, segment)

    # Segment aggregations
    segments = (
        df.groupby("segment")
        .agg(
            ingresos=("sales", "sum"),
            ordenes=("order_id", "nunique"),
            clientes=("customer_name", "nunique"),
            total_profit=("profit", "sum"),
            avg_discount=("discount", "mean"),
        )
        .reset_index()
    )
    seg_list = []
    for _, row in segments.iterrows():
        avg_order = row["ingresos"] / row["ordenes"] if row["ordenes"] else 0
        margin = round(row["total_profit"] / row["ingresos"] * 100, 1) if row["ingresos"] else 0
        seg_list.append({
            "segmento": row["segment"],
            "clientes": int(row["clientes"]),
            "ingresos": round(float(row["ingresos"]), 2),
            "ingresos_fmt": fmt_dollar(float(row["ingresos"])),
            "ordenes": int(row["ordenes"]),
            "avg_order": round(float(avg_order), 2),
            "avg_order_fmt": fmt_dollar(float(avg_order)),
            "margin": margin,
            "avg_discount": round(float(row["avg_discount"]) * 100, 1),
        })

    # Top 10 customers by revenue
    cust = (
        df.groupby(["customer_name", "segment"])
        .agg(
            revenue=("sales", "sum"),
            orders=("order_id", "nunique"),
            profit=("profit", "sum"),
        )
        .reset_index()
    )
    cust["ticket"] = cust["revenue"] / cust["orders"]
    cust["margin"] = (cust["profit"] / cust["revenue"] * 100).round(1)
    top = cust.sort_values("revenue", ascending=False).head(10)

    top_customers = []
    for i, (_, row) in enumerate(top.iterrows()):
        top_customers.append({
            "rank": i + 1,
            "name": row["customer_name"],
            "segment": row["segment"],
            "revenue": round(float(row["revenue"]), 2),
            "revenue_fmt": fmt_dollar(float(row["revenue"])),
            "orders": int(row["orders"]),
            "ticket": round(float(row["ticket"]), 2),
            "ticket_fmt": fmt_dollar(float(row["ticket"])),
            "margin": float(row["margin"]),
        })

    # Insight
    top_seg = segments.sort_values("ingresos", ascending=False)
    top_seg_name = top_seg.iloc[0]["segment"] if len(top_seg) else None
    avg_total = float(df["sales"].sum() / df["order_id"].nunique()) if df["order_id"].nunique() else 0

    return {
        "chart_segment": build_segment_distribution(df, theme),
        "chart_frequency": build_customer_frequency(df, theme),
        "chart_segment_margin": build_segment_margin(df, theme),
        "segments": seg_list,
        "top_customers": top_customers,
        "insight": {
            "top_segment": top_seg_name,
            "top_ingresos": fmt_dollar(float(top_seg.iloc[0]["ingresos"])) if len(top_seg) else "—",
            "avg_ticket": fmt_dollar(avg_total),
            "total_customers": int(df["customer_name"].nunique()),
            "repeat_rate": round(
                cust[cust["orders"] > 1].shape[0] / cust.shape[0] * 100, 1
            ) if cust.shape[0] else 0,
        } if top_seg_name else None,
        "filtered_orders": int(df["order_id"].nunique()),
    }
