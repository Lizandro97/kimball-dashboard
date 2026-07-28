"""GET /api/shipping — Analisis de Envios."""

from fastapi import APIRouter, Query

from api.services.chart_service import (
    build_delivery_histogram,
    build_shipping_by_region,
    build_shipping_mode_impact,
    calc_shipping_kpis_by_region,
    calc_shipping_stats,
    filter_data,
    load_data,
)

router = APIRouter()


@router.get("/shipping")
def get_shipping(
    region: str = Query("Todas"),
    year: str = Query("Todos"),
    segment: str = Query("Todos"),
    theme: str = Query("light"),
):
    df = filter_data(load_data(), region, year, segment)
    stats = calc_shipping_stats(df)
    return {
        "stats": stats,
        "region_kpis": calc_shipping_kpis_by_region(df),
        "chart_by_region": build_shipping_by_region(df, theme),
        "chart_mode_impact": build_shipping_mode_impact(df, theme),
        "chart_histogram": build_delivery_histogram(df, theme),
        "filtered_orders": int(df["order_id"].nunique()),
    }
