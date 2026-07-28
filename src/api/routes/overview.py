"""GET /api/overview — Resumen Ejecutivo."""

from fastapi import APIRouter, Query

from api.services.chart_service import (
    build_category_bar_mini,
    build_mom_comparison,
    build_monthly_trend,
    build_pareto_products,
    build_region_donut,
    build_top5_products,
    calc_quantity_stats,
    filter_data,
    fmt_dollar,
    load_data,
)

router = APIRouter()


@router.get("/overview")
def get_overview(
    region: str = Query("Todas"),
    year: str = Query("Todos"),
    segment: str = Query("Todos"),
    theme: str = Query("light"),
):
    df_global = load_data()
    df = filter_data(df_global, region, year, segment)

    total_sales = float(df["sales"].sum())
    total_profit = float(df["profit"].sum())
    total_orders = int(df["order_id"].nunique())
    total_customers = int(df["customer_name"].nunique())
    margin = round(total_profit / total_sales * 100, 1) if total_sales else 0

    # YoY: compare against the last complete year before the latest year in the dataset
    years_in_data = sorted(df_global["order_date"].dt.year.dropna().unique().astype(int))
    if year != "Todos":
        current_year = int(year)
        prev_year = current_year - 1
        df_prev = filter_data(df_global, region, str(prev_year), segment)
    elif len(years_in_data) >= 2:
        current_year = years_in_data[-1]
        prev_year = years_in_data[-2]
        df_prev = filter_data(df_global, region, str(prev_year), segment)
    else:
        df_prev = df_global.iloc[0:0]
        prev_sales = prev_profit = prev_orders = 0.0
        prev_margin = 0.0

    if year != "Todos" or len(years_in_data) >= 2:
        prev_sales = float(df_prev["sales"].sum())
        prev_profit = float(df_prev["profit"].sum())
        prev_orders = int(df_prev["order_id"].nunique())
        prev_margin = round(prev_profit / prev_sales * 100, 1) if prev_sales else 0

    def yoy(current, previous):
        if previous == 0:
            return None
        return round((current - previous) / previous * 100, 1)

    qty = calc_quantity_stats(df)

    # Alerts
    discount_loss = float(df[df["discount"] > 0.5]["profit"].sum())
    df_south = filter_data(df_global, "South", year, segment)
    south_margin = round(
        df_south["profit"].sum() / df_south["sales"].sum() * 100, 1
    ) if df_south["sales"].sum() else 0
    df_tech = filter_data(df_global, region, year, "Todos")
    tech = df_tech[df_tech["category"] == "Technology"]
    tech_margin = round(
        tech["profit"].sum() / tech["sales"].sum() * 100, 1
    ) if tech["sales"].sum() else 0

    return {
        "kpis": {
            "total_sales": total_sales,
            "total_sales_fmt": fmt_dollar(total_sales),
            "total_profit": total_profit,
            "total_profit_fmt": fmt_dollar(total_profit),
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_fact_rows": int(df_global["order_id"].count()),
            "margin": margin,
            "yoy_sales": yoy(total_sales, prev_sales),
            "yoy_profit": yoy(total_profit, prev_profit),
            "yoy_orders": yoy(total_orders, prev_orders),
            "yoy_margin": round(margin - prev_margin, 1),
            "total_units": qty["total_units"],
            "avg_qty_per_order": qty["avg_per_order"],
        },
        "chart_monthly_trend": build_monthly_trend(df if len(df) > 10 else df_global, theme),
        "chart_region_donut": build_region_donut(df, theme),
        "chart_category": build_category_bar_mini(df, theme),
        "top5_products": build_top5_products(df),
        "pareto": build_pareto_products(df),
        "mom": build_mom_comparison(df, theme),
        "alerts": {
            "discount_loss": discount_loss,
            "discount_loss_fmt": fmt_dollar(discount_loss),
            "south_margin": south_margin,
            "tech_margin": tech_margin,
        },
    }
