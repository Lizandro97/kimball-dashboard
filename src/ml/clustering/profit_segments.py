import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ml import load_data


def segment_profitability() -> dict:
    df = load_data()

    grid = (
        df.groupby(["Region", "Category", "Segment"])
        .agg(
            sales=("Sales", "sum"),
            profit=("Profit", "sum"),
            discount_avg=("Discount", "mean"),
            order_count=("Order ID", "nunique"),
            quantity=("Quantity", "sum"),
        )
        .reset_index()
    )
    grid["margin"] = (grid["profit"] / grid["sales"] * 100).fillna(0).clip(-200, 200)
    grid["sales"] = grid["sales"].clip(lower=0.01)

    features = grid[["profit", "margin", "discount_avg", "order_count"]].copy().fillna(0)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    n_clusters = 4
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model.fit(scaled)
    grid["cluster"] = model.labels_.tolist()

    profile = grid.groupby("cluster").agg(
        count=("Region", "count"),
        avg_profit=("profit", "mean"),
        avg_margin=("margin", "mean"),
        avg_discount=("discount_avg", "mean"),
    ).reset_index()

    cluster_order = sorted(
        range(n_clusters),
        key=lambda c: profile[profile["cluster"] == c]["avg_profit"].iloc[0],
        reverse=True,
    )

    labels_map = {
        0: "Alta Rentabilidad",
        1: "Rentabilidad Media",
        2: "Baja Rentabilidad",
        3: "Pérdida",
    }

    segments = []
    for rank, c in enumerate(cluster_order):
        row = profile[profile["cluster"] == c].iloc[0]
        segments.append({
            "cluster": int(c),
            "label": labels_map.get(rank, f"Cluster {c}"),
            "rank": rank + 1,
            "combinaciones": int(row["count"]),
            "avg_profit": round(row["avg_profit"], 2),
            "avg_profit_fmt": f"${row['avg_profit']:,.0f}",
            "avg_margin_pct": round(row["avg_margin"], 1),
            "avg_discount_pct": round(row["avg_discount"] * 100, 1),
        })

    heatmap = []
    for _, row in grid.iterrows():
        heatmap.append({
            "region": row["Region"],
            "category": row["Category"],
            "segment": row["Segment"],
            "profit": round(row["profit"], 2),
            "profit_fmt": f"${row['profit']:,.0f}",
            "margin": round(row["margin"], 1),
            "discount_avg": round(row["discount_avg"] * 100, 1),
            "sales": round(row["sales"], 2),
            "orders": int(row["order_count"]),
            "cluster": int(row["cluster"]),
            "cluster_label": next(s["label"] for s in segments if s["cluster"] == row["cluster"]),
        })

    return {"segments": segments, "heatmap": heatmap}
