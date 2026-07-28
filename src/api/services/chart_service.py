"""Plotly chart builders for the BI dashboard (replaces matplotlib)."""

import json
import warnings
from functools import lru_cache

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils

from components.charts import filter_data  # noqa: F401  re-exported
from components.charts import load_data as _load_data_raw

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")




@lru_cache(maxsize=1)
def load_data():
    return _load_data_raw()


def fix_numpy(obj):
    if isinstance(obj, (np.ndarray, pd.Series)):
        return obj.tolist()
    if isinstance(obj, dict):
        if "bdata" in obj and "dtype" in obj:
            import base64
            return np.frombuffer(base64.b64decode(obj["bdata"]), dtype=obj["dtype"]).tolist()
        return {k: fix_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fix_numpy(v) for v in obj]
    return obj


def _to_json_safe(fig):
    fig = fix_numpy(fig)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

BLUE = "#2563eb"
TEAL = "#0d9488"
AMBER = "#d97706"
ROSE = "#e11d48"
GREEN = "#059669"
RED = "#dc2626"
PURPLE = "#7c3aed"
GRAY = "#94a3b8"

CAT_COLORS = {"Technology": BLUE, "Office Supplies": TEAL, "Furniture": AMBER}
REGION_COLORS = {"West": BLUE, "East": PURPLE, "Central": AMBER, "South": ROSE}
SEGMENT_COLORS = {"Consumer": BLUE, "Corporate": TEAL, "Home Office": PURPLE}

STATE_ABBR = {
    "Alabama": "AL", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}


def _template(theme: str) -> str:
    return "plotly_dark" if theme == "dark" else "plotly_white"


def fmt_dollar(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"


def build_monthly_trend(df: pd.DataFrame, theme: str = "light") -> dict:
    monthly = df.set_index("order_date").resample("ME")["sales"].sum().reset_index()
    ma = monthly.copy()
    ma["ma"] = monthly["sales"].rolling(3, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["order_date"], y=monthly["sales"],
        mode="lines+markers", name="Ingresos",
        line={"color": BLUE, "width": 2},
        marker={"size": 4},
    ))
    fig.add_trace(go.Scatter(
        x=ma["order_date"], y=ma["ma"],
        mode="lines", name="Media móvil (3m)",
        line={"color": ROSE, "width": 1.5, "dash": "dash"},
    ))
    fig.update_layout(
        title="Ingresos Mensuales",
        template=_template(theme),
        yaxis={"title": "Ventas", "tickprefix": "$"},
        hovermode="x unified",
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        height=320,
        legend={"orientation": "h", "y": 1.1},
    )
    return _to_json_safe(fig.to_dict())


def build_sales_by_category(df: pd.DataFrame, theme: str = "light") -> dict:
    data = df.groupby("category")["sales"].sum().reset_index().sort_values("sales", ascending=False)
    fig = px.bar(
        data, x="category", y="sales",
        color="category", color_discrete_map=CAT_COLORS,
        title="Ventas por Categoría",
        text=data["sales"].apply(fmt_dollar),
    )
    fig.update_traces(textposition="auto", textfont_size=11)
    fig.update_layout(
        template=_template(theme),
        showlegend=False,
        yaxis={"title": "Ventas", "tickprefix": "$"},
        height=340,
    )
    return _to_json_safe(fig.to_dict())


def build_sales_by_region(df: pd.DataFrame, theme: str = "light") -> dict:
    data = df.groupby("region")["sales"].sum().reset_index().sort_values("sales", ascending=False)
    fig = px.bar(
        data, x="region", y="sales",
        color="region", color_discrete_map=REGION_COLORS,
        title="Ventas por Región",
        text=data["sales"].apply(fmt_dollar),
    )
    fig.update_traces(textposition="auto", textfont_size=11)
    fig.update_layout(
        template=_template(theme),
        showlegend=False,
        yaxis={"title": "Ventas", "tickprefix": "$"},
        height=340,
    )
    return _to_json_safe(fig.to_dict())


def build_profit_by_discount(df: pd.DataFrame, theme: str = "light") -> dict:
    def tier(d):
        if d == 0:
            return "Sin desc."
        if d <= 0.2:
            return "≤20%"
        if d <= 0.5:
            return "≤50%"
        return ">50%"

    data = df.copy()
    data["tier"] = data["discount"].apply(tier)
    tier_order = ["Sin desc.", "≤20%", "≤50%", ">50%"]
    grouped = data.groupby("tier", observed=True)["profit"].sum().reindex(tier_order).reset_index()
    grouped.columns = ["tier", "profit"]

    colors = [GREEN if v >= 0 else RED for v in grouped["profit"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grouped["tier"], y=grouped["profit"],
        marker_color=colors,
        text=grouped["profit"].apply(fmt_dollar),
        textposition="auto",
        textfont_size=11,
    ))
    fig.add_hline(y=0, line={"color": GRAY, "width": 1})
    fig.update_layout(
        title="Utilidad por Nivel de Descuento",
        template=_template(theme),
        yaxis={"title": "Utilidad", "tickprefix": "$"},
        height=300,
    )
    return _to_json_safe(fig.to_dict())


def build_profit_by_region_category(df: pd.DataFrame, theme: str = "light") -> dict:
    pivot = df.groupby(["region", "category"])["profit"].sum().reset_index()
    fig = px.bar(
        pivot, x="region", y="profit", color="category",
        barmode="group", color_discrete_map=CAT_COLORS,
        title="Utilidad por Región y Categoría",
    )
    fig.update_layout(
        template=_template(theme),
        yaxis={"title": "Utilidad", "tickprefix": "$"},
        height=340,
        legend={"orientation": "h", "y": 1.1},
    )
    return _to_json_safe(fig.to_dict())


def build_segment_distribution(df: pd.DataFrame, theme: str = "light") -> dict:
    data = df.groupby("segment")["sales"].sum().reset_index()
    fig = px.pie(
        data, values="sales", names="segment",
        color="segment", color_discrete_map=SEGMENT_COLORS,
        title="Distribución de Ventas por Segmento",
        hole=0.4,
    )
    fig.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Ventas: $%{value:,.0f}<br>%{percent}",
    )
    fig.update_layout(
        template=_template(theme),
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        height=320,
        showlegend=False,
    )
    return _to_json_safe(fig.to_dict())


# ── New chart builders ─────────────────────────────────────────


def calc_shipping_stats(df: pd.DataFrame) -> dict:
    d = df[["order_date", "ship_date", "ship_mode"]].dropna().copy()
    d["delivery_days"] = (d["ship_date"] - d["order_date"]).dt.days
    avg = d["delivery_days"].mean()
    on_time_pct = (d["delivery_days"] <= 5).mean() * 100
    by_mode = d.groupby("ship_mode")["delivery_days"].agg(["mean", "count", "std"]).round(1)
    return {
        "avg_delivery_days": round(avg, 1),
        "on_time_pct": round(on_time_pct, 1),
        "total_orders": int(d["ship_date"].count()),
        "by_mode": {
            mode: {
                "avg": int(row["mean"]),
                "orders": int(row["count"]),
            }
            for mode, row in by_mode.iterrows()
        },
    }


def build_delivery_histogram(df: pd.DataFrame, theme: str = "light") -> dict:
    d = df[["order_date", "ship_date", "ship_mode"]].dropna().copy()
    d["delivery_days"] = (d["ship_date"] - d["order_date"]).dt.days
    data = d.groupby(["delivery_days", "ship_mode"]).size().reset_index(name="orders")
    fig = px.bar(
        data, x="delivery_days", y="orders", color="ship_mode",
        barmode="stack",
        title="Distribución de Tiempos de Entrega",
        labels={"delivery_days": "Días", "orders": "Órdenes", "ship_mode": "Modo de Envío"},
    )
    fig.update_layout(
        template=_template(theme),
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        height=320,
        legend={"orientation": "h", "y": 1.1},
    )
    return _to_json_safe(fig.to_dict())


def build_shipping_monthly(df: pd.DataFrame, theme: str = "light") -> dict:
    d = df[["order_date", "ship_date"]].dropna().copy()
    d["month"] = d["order_date"].dt.to_period("M").astype(str)
    monthly = d.groupby("month").size().reset_index(name="orders")
    fig = px.line(
        monthly, x="month", y="orders",
        markers=True, title="Órdenes por Mes",
        labels={"month": "", "orders": "Órdenes"},
    )
    fig.update_traces(line={"color": BLUE, "width": 2}, marker={"size": 4, "color": BLUE})
    fig.update_layout(
        template=_template(theme),
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        height=300,
    )
    return _to_json_safe(fig.to_dict())


def build_state_map(df: pd.DataFrame, theme: str = "light") -> dict:
    state_data = df.groupby("state")[["sales", "profit"]].sum().reset_index()
    state_data["abbr"] = state_data["state"].map(STATE_ABBR)
    state_data.dropna(subset=["abbr"], inplace=True)
    fig = px.choropleth(
        state_data,
        locations="abbr",
        locationmode="USA-states",
        color="sales",
        scope="usa",
        title="Ventas por Estado",
        color_continuous_scale="Blues",
        labels={"sales": "Ventas"},
        hover_data={"profit": ":.0f", "abbr": False, "state": True},
    )
    fig.update_layout(
        template=_template(theme),
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=400,
        geo={"bgcolor": "rgba(0,0,0,0)"},
    )
    return _to_json_safe(fig.to_dict())


def build_sales_by_subcategory(df: pd.DataFrame, theme: str = "light") -> dict:
    data = df.groupby("sub_category")["sales"].sum().reset_index().sort_values("sales", ascending=False).head(15)
    fig = px.bar(
        data, x="sales", y="sub_category",
        orientation="h",
        title="Top 15 Subcategorías por Ventas",
        text=data["sales"].apply(fmt_dollar),
        color="sales", color_continuous_scale="Blues",
    )
    fig.update_traces(textposition="auto", textfont_size=11)
    fig.update_layout(
        template=_template(theme),
        yaxis={"title": "", "autorange": "reversed"},
        xaxis={"title": "Ventas", "tickprefix": "$"},
        margin={"l": 10, "r": 60, "t": 40, "b": 30},
        height=400,
        showlegend=False,
    )
    return _to_json_safe(fig.to_dict())


def calc_quantity_stats(df: pd.DataFrame) -> dict:
    total_units = int(df["quantity"].sum())
    avg_per_order = round(df.groupby("order_id")["quantity"].sum().mean(), 1)
    by_category = df.groupby("category")["quantity"].sum().to_dict()
    return {
        "total_units": total_units,
        "avg_per_order": avg_per_order,
        "by_category": by_category,
    }


def build_customer_frequency(df: pd.DataFrame, theme: str = "light") -> dict:
    cust = df.groupby("customer_name")["order_id"].nunique().reset_index()
    cust.columns = ["customer", "orders"]

    bins = [(1, 1, "1"), (2, 3, "2-3"), (4, 5, "4-5"), (6, 10, "6-10"), (11, 50, "11+")]
    freq_data = []
    for lo, hi, label in bins:
        count = cust[(cust["orders"] >= lo) & (cust["orders"] <= hi)].shape[0]
        freq_data.append({"range": label, "count": count})

    fig = go.Figure(go.Bar(
        x=[d["range"] for d in freq_data],
        y=[d["count"] for d in freq_data],
        marker_color=[BLUE, TEAL, AMBER, PURPLE, ROSE],
        text=[str(d["count"]) for d in freq_data],
        textposition="auto",
        textfont_size=11,
    ))
    fig.update_layout(
        title="Distribucion de Clientes por Frecuencia de Compra",
        template=_template(theme),
        xaxis={"title": "Ordenes por Cliente"},
        yaxis={"title": "Clientes"},
        height=340,
    )
    return _to_json_safe(fig.to_dict())


def build_segment_margin(df: pd.DataFrame, theme: str = "light") -> dict:
    seg = (
        df.groupby("segment")
        .agg(revenue=("sales", "sum"), profit=("profit", "sum"), avg_discount=("discount", "mean"))
        .reset_index()
    )
    seg["margin"] = (seg["profit"] / seg["revenue"] * 100).round(1)
    seg["avg_discount"] = (seg["avg_discount"] * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=seg["segment"], y=seg["margin"],
        name="Margen %",
        marker_color=BLUE,
        text=seg["margin"].apply(lambda v: f"{v}%"),
        textposition="auto",
        textfont_size=11,
    ))
    fig.add_trace(go.Bar(
        x=seg["segment"], y=seg["avg_discount"],
        name="Descuento Avg %",
        marker_color=AMBER,
        text=seg["avg_discount"].apply(lambda v: f"{v}%"),
        textposition="auto",
        textfont_size=11,
    ))
    fig.update_layout(
        title="Margen y Descuento por Segmento",
        template=_template(theme),
        barmode="group",
        yaxis={"title": "Porcentaje", "ticksuffix": "%"},
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
        height=320,
        legend={"orientation": "h", "y": 1.1},
    )
    return _to_json_safe(fig.to_dict())


# ── Overview mini charts ──────────────────────────────────────────────

def build_region_donut(df: pd.DataFrame, theme: str = "light") -> dict:
    data = df.groupby("region")["sales"].sum().reset_index().sort_values("sales", ascending=False)
    fig = px.pie(
        data, values="sales", names="region",
        color="region", color_discrete_map=REGION_COLORS,
        hole=0.5,
    )
    fig.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Ventas: $%{value:,.0f}<br>%{percent}",
    )
    fig.update_layout(
        title="Ventas por Region",
        template=_template(theme),
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=280,
        showlegend=False,
    )
    return _to_json_safe(fig.to_dict())


def build_category_bar_mini(df: pd.DataFrame, theme: str = "light") -> dict:
    data = df.groupby("category")["sales"].sum().reset_index().sort_values("sales", ascending=False)
    fig = px.bar(
        data, x="category", y="sales",
        color="category", color_discrete_map=CAT_COLORS,
        text=data["sales"].apply(fmt_dollar),
    )
    fig.update_traces(textposition="auto", textfont_size=11)
    fig.update_layout(
        title="Ventas por Categoria",
        template=_template(theme),
        showlegend=False,
        yaxis={"title": "Ventas", "tickprefix": "$"},
        height=300,
    )
    return _to_json_safe(fig.to_dict())


def build_top5_products(df: pd.DataFrame) -> list:
    top = (
        df.groupby(["product_name", "category"])
        .agg(revenue=("sales", "sum"), profit=("profit", "sum"))
        .sort_values("revenue", ascending=False)
        .head(5)
        .reset_index()
    )
    result = []
    for _, row in top.iterrows():
        margin = round(row["profit"] / row["revenue"] * 100, 1) if row["revenue"] else 0
        result.append({
            "name": row["product_name"],
            "category": row["category"],
            "revenue_fmt": fmt_dollar(row["revenue"]),
            "margin": margin,
        })
    return result


# ── Shipping redesigned charts ────────────────────────────────────────

def build_shipping_by_region(df: pd.DataFrame, theme: str = "light") -> dict:
    d = df[["order_date", "ship_date", "region"]].dropna().copy()
    d["delivery_days"] = (d["ship_date"] - d["order_date"]).dt.days
    by_region = d.groupby("region")["delivery_days"].mean().reset_index()
    by_region.columns = ["region", "avg_days"]
    by_region = by_region.sort_values("avg_days", ascending=False)

    colors = [REGION_COLORS.get(r, BLUE) for r in by_region["region"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=by_region["region"], y=by_region["avg_days"],
        marker_color=colors,
        text=by_region["avg_days"].apply(lambda v: f"{v:.1f}d"),
        textposition="auto",
        textfont_size=11,
    ))
    fig.update_layout(
        title="Tiempo Promedio de Entrega por Region",
        template=_template(theme),
        yaxis={"title": "Dias promedio"},
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        height=300,
    )
    return _to_json_safe(fig.to_dict())


def build_shipping_mode_impact(df: pd.DataFrame, theme: str = "light") -> dict:
    mode_data = df.groupby("ship_mode").agg(
        revenue=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index()
    mode_data["margin"] = (mode_data["profit"] / mode_data["revenue"] * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=mode_data["ship_mode"], y=mode_data["revenue"],
        name="Ingresos", marker_color=BLUE,
        text=mode_data["revenue"].apply(fmt_dollar),
        textposition="auto",
        textfont_size=11,
    ))
    fig.add_trace(go.Bar(
        x=mode_data["ship_mode"], y=mode_data["profit"],
        name="Utilidad", marker_color=GREEN,
        text=mode_data["profit"].apply(fmt_dollar),
        textposition="auto",
        textfont_size=11,
    ))
    fig.update_layout(
        title="Ingresos y Utilidad por Modo de Envio",
        template=_template(theme),
        barmode="group",
        yaxis={"title": "Monto", "tickprefix": "$"},
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        height=300,
        legend={"orientation": "h", "y": 1.1},
    )
    return _to_json_safe(fig.to_dict())


def calc_shipping_kpis_by_region(df: pd.DataFrame) -> list:
    d = df[["order_date", "ship_date", "region"]].dropna().copy()
    d["delivery_days"] = (d["ship_date"] - d["order_date"]).dt.days
    by_region = d.groupby("region").agg(
        avg_days=("delivery_days", "mean"),
        on_time=("delivery_days", lambda x: (x <= 5).mean() * 100),
        orders=("delivery_days", "count"),
    ).round(1).reset_index()
    return [
        {
            "region": row["region"],
            "avg_days": round(row["avg_days"], 1),
            "on_time_pct": round(row["on_time"], 1),
            "orders": int(row["orders"]),
        }
        for _, row in by_region.iterrows()
    ]


# ── Pareto 80/20 Analysis ──────────────────────────────────────────────

def build_pareto_products(df: pd.DataFrame) -> dict:
    top = (
        df.groupby("product_name")
        .agg(revenue=("sales", "sum"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )
    total = top["revenue"].sum()
    top["cum_pct"] = top["revenue"].cumsum() / total * 100
    top["product_pct"] = (top.index + 1) / len(top) * 100
    pareto_line = top[top["product_pct"].between(15, 25)].iloc[0] if len(top) >= 20 else top.iloc[min(5, len(top)-1)]
    pct_products = round(pareto_line["product_pct"], 1)
    pct_revenue = round(pareto_line["cum_pct"], 1)
    top20 = top.head(max(1, int(len(top) * 0.2)))
    top20_revenue_share = round(top20["revenue"].sum() / total * 100, 1)
    return {
        "total_products": len(top),
        "top20_products_count": len(top20),
        "top20_revenue_share": top20_revenue_share,
        "pct_products_for_80": pct_products,
        "pct_revenue_from_top": pct_revenue,
        "items": top.head(10).to_dict("records"),
    }


def build_pareto_customers(df: pd.DataFrame) -> dict:
    top = (
        df.groupby("customer_name")
        .agg(revenue=("sales", "sum"), orders=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )
    total = top["revenue"].sum()
    top20 = top.head(max(1, int(len(top) * 0.2)))
    top20_revenue_share = round(top20["revenue"].sum() / total * 100, 1)
    return {
        "total_customers": len(top),
        "top20_customers_count": len(top20),
        "top20_revenue_share": top20_revenue_share,
    }


# ── Time Intelligence MoM ──────────────────────────────────────────────

def build_mom_comparison(df: pd.DataFrame, theme: str = "light") -> dict:
    monthly = df.set_index("order_date").resample("ME")["sales"].sum().reset_index()
    if len(monthly) < 2:
        return {"has_data": False}
    monthly["mom_change"] = monthly["sales"].pct_change() * 100
    monthly["mom_label"] = monthly["order_date"].dt.strftime("%b %Y")
    last = monthly.iloc[-1]
    prev = monthly.iloc[-2]
    return {
        "has_data": True,
        "current_month": last["mom_label"],
        "current_sales": float(last["sales"]),
        "current_fmt": fmt_dollar(float(last["sales"])),
        "prev_month": prev["mom_label"],
        "prev_sales": float(prev["sales"]),
        "prev_fmt": fmt_dollar(float(prev["sales"])),
        "mom_pct": round(float(last["mom_change"]), 1),
        "chart": _to_json_safe(go.Figure(
            data=[
                go.Bar(name="Mes Actual", x=[last["mom_label"]], y=[last["sales"]],
                       marker_color=BLUE, text=[fmt_dollar(float(last["sales"]))], textposition="auto", textfont_size=11),
                go.Bar(name="Mes Anterior", x=[prev["mom_label"]], y=[prev["sales"]],
                       marker_color=GRAY, text=[fmt_dollar(float(prev["sales"]))], textposition="auto", textfont_size=11),
            ],
            layout={
                "title": "Comparacion Mensual (MoM)",
                "template": _template(theme),
                "barmode": "group",
                "height": 260,
                "margin": {"l": 30, "r": 10, "t": 30, "b": 20},
                "showlegend": True,
                "legend": {"orientation": "h", "y": 1.1},
            },
        ).to_dict()),
    }


# ── Geographic Drill-down by City ─────────────────────────────────────

def build_sales_by_city(df: pd.DataFrame, theme: str = "light") -> dict:
    city_data = df.groupby(["state", "city"])["sales"].sum().reset_index().sort_values("sales", ascending=False).head(15)
    city_data["location"] = city_data["city"] + ", " + city_data["state"]
    fig = px.bar(
        city_data, x="sales", y="location",
        orientation="h", title="Top 15 Ciudades por Ventas",
        text=city_data["sales"].apply(fmt_dollar),
        color="sales", color_continuous_scale="Blues",
    )
    fig.update_traces(textposition="auto", textfont_size=11)
    fig.update_layout(
        template=_template(theme),
        yaxis={"title": "", "autorange": "reversed"},
        xaxis={"title": "Ventas", "tickprefix": "$"},
        margin={"l": 10, "r": 60, "t": 40, "b": 30},
        height=400,
        showlegend=False,
    )
    return _to_json_safe(fig.to_dict())
