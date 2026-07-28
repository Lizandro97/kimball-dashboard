from fastapi import APIRouter, Query

from api.services.chart_service import (
    build_monthly_trend,
    build_sales_by_category,
    build_sales_by_city,
    build_sales_by_region,
    build_sales_by_subcategory,
    build_state_map,
    filter_data,
    fmt_dollar,
    load_data,
)

router = APIRouter()


@router.get("/sales")
def get_sales(
    region: str = Query("Todas"),
    year: str = Query("Todos"),
    segment: str = Query("Todos"),
    theme: str = Query("light"),
):
    df_global = load_data()
    df = filter_data(df_global, region, year, segment)

    top = (
        df.groupby(["product_name", "category", "sub_category"])
        .agg(ventas=("sales", "sum"), utilidad=("profit", "sum"))
        .assign(margen=lambda x: (x["utilidad"] / x["ventas"] * 100).round(1))
        .sort_values("ventas", ascending=False)
        .head(10)
        .reset_index()
    )
    top_products = []
    for _, row in top.iterrows():
        top_products.append({
            "producto": row["product_name"],
            "categoria": row["category"],
            "subcategoria": row["sub_category"],
            "ventas": round(float(row["ventas"]), 2),
            "ventas_fmt": fmt_dollar(float(row["ventas"])),
            "utilidad": round(float(row["utilidad"]), 2),
            "utilidad_fmt": fmt_dollar(float(row["utilidad"])),
            "margen": float(row["margen"]),
        })

    return {
        "chart_category": build_sales_by_category(df, theme),
        "chart_region": build_sales_by_region(df, theme),
        "chart_monthly": build_monthly_trend(df if len(df) > 10 else df_global, theme),
        "chart_subcategory": build_sales_by_subcategory(df, theme),
        "chart_map": build_state_map(df, theme),
        "chart_city": build_sales_by_city(df, theme),
        "top_products": top_products,
        "filtered_orders": int(df["order_id"].nunique()),
    }
