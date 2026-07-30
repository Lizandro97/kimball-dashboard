import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ml import load_data


def segment_products() -> dict:
    df = load_data()

    prod = (
        df.groupby("Product Name")
        .agg(
            category=("Category", "first"),
            sub_category=("Sub-Category", "first"),
            sales=("Sales", "sum"),
            profit=("Profit", "sum"),
            discount_avg=("Discount", "mean"),
            order_count=("Order ID", "nunique"),
            quantity=("Quantity", "sum"),
        )
        .reset_index()
    )
    prod["margin"] = (prod["profit"] / prod["sales"] * 100).fillna(0).clip(-200, 200)
    prod["sales"] = prod["sales"].clip(lower=0.01)

    features = prod[["sales", "profit", "discount_avg", "order_count", "margin"]].copy()
    features[["sales", "profit", "order_count"]] = features[["sales", "profit", "order_count"]].clip(lower=0)
    features[["sales", "profit", "order_count"]] = np.log1p(
        features[["sales", "profit", "order_count"]]
    )
    features = features.fillna(0)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    n_clusters = 4
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model.fit(scaled)
    prod["cluster"] = model.labels_.tolist()

    profile = prod.groupby("cluster").agg(
        count=("Product Name", "count"),
        avg_sales=("sales", "mean"),
        avg_profit=("profit", "mean"),
        avg_margin=("margin", "mean"),
        avg_discount=("discount_avg", "mean"),
    ).reset_index()

    centroids = scaler.inverse_transform(np.expm1(model.cluster_centers_))
    cluster_order = sorted(
        range(n_clusters),
        key=lambda c: centroids[c][0] * (centroids[c][1] + 100),
        reverse=True,
    )

    labels_map = {
        0: "Estrella",
        1: "Volumen",
        2: "Potencial",
        3: "Lastre",
    }

    segments = []
    for rank, c in enumerate(cluster_order):
        row = profile[profile["cluster"] == c].iloc[0]
        segments.append({
            "cluster": int(c),
            "label": labels_map.get(rank, f"Cluster {c}"),
            "rank": rank + 1,
            "productos": int(row["count"]),
            "avg_sales": round(row["avg_sales"], 2),
            "avg_sales_fmt": f"${row['avg_sales']:,.0f}",
            "avg_profit": round(row["avg_profit"], 2),
            "avg_profit_fmt": f"${row['avg_profit']:,.0f}",
            "avg_margin_pct": round(row["avg_margin"], 1),
            "avg_discount_pct": round(row["avg_discount"] * 100, 1),
        })

    scatter = []
    for _, row in prod.iterrows():
        scatter.append({
            "producto": row["Product Name"][:60],
            "categoria": row["category"],
            "subcategoria": row["sub_category"],
            "sales": round(row["sales"], 2),
            "sales_fmt": f"${row['sales']:,.0f}",
            "profit": round(row["profit"], 2),
            "profit_fmt": f"${row['profit']:,.0f}",
            "margin": round(row["margin"], 1),
            "discount_avg": round(row["discount_avg"] * 100, 1),
            "order_count": int(row["order_count"]),
            "cluster": int(row["cluster"]),
            "cluster_label": next(s["label"] for s in segments if s["cluster"] == row["cluster"]),
        })

    return {"segments": segments, "scatter": scatter}
