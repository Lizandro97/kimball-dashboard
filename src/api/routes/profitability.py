"""GET /api/profitability — Rentabilidad."""

from fastapi import APIRouter, Query

from api.services.chart_service import (
    build_profit_by_discount,
    build_profit_by_region_category,
    filter_data,
    fmt_dollar,
    load_data,
)

router = APIRouter()


@router.get("/profitability")
def get_profitability(
    region: str = Query("Todas"),
    year: str = Query("Todos"),
    segment: str = Query("Todos"),
    theme: str = Query("light"),
):
    df_global = load_data()
    df = filter_data(df_global, region, year, segment)

    discount_loss = float(df[df["discount"] > 0.5]["profit"].sum())
    discount_pct = round(len(df[df["discount"] > 0.5]) / len(df) * 100, 1) if len(df) else 0

    # Discount tiers summary (for the insight sidebar)
    def tier(d):
        if d == 0:
            return "Sin desc."
        if d <= 0.2:
            return "≤20%"
        if d <= 0.5:
            return "≤50%"
        return ">50%"
    df_copy = df.copy()
    df_copy["tier"] = df_copy["discount"].apply(tier)
    tier_order = ["Sin desc.", "≤20%", "≤50%", ">50%"]
    summary = (
        df_copy.groupby("tier", observed=True)
        .agg(transacciones=("sales", "count"), utilidad=("profit", "sum"))
        .reindex(tier_order)
        .reset_index()
    )
    tiers = []
    for _, row in summary.iterrows():
        tiers.append({
            "nivel": row["tier"],
            "transacciones": int(row["transacciones"]),
            "utilidad": round(float(row["utilidad"]), 2),
            "utilidad_fmt": fmt_dollar(float(row["utilidad"])),
        })

    # Most profitable combination
    winner = (
        df.groupby(["region", "category"])["profit"].sum()
        .reset_index().sort_values("profit", ascending=False)
    )
    winner_row = winner.iloc[0] if len(winner) else None

    return {
        "discount_loss": discount_loss,
        "discount_loss_fmt": fmt_dollar(discount_loss),
        "discount_pct": discount_pct,
        "chart_discount": build_profit_by_discount(df, theme),
        "chart_region_category": build_profit_by_region_category(df, theme),
        "tiers": tiers,
        "winner": {
            "region": winner_row["region"],
            "category": winner_row["category"],
            "profit": fmt_dollar(float(winner_row["profit"])),
        } if winner_row is not None else None,
        "filtered_orders": int(df["order_id"].nunique()),
    }
