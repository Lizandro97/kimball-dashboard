from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ml import load_data


def compute_rfm() -> pd.DataFrame:
    df = load_data()
    ref_date = df["Order Date"].max() + timedelta(days=1)

    rfm = (
        df.groupby("Customer ID")
        .agg(
            customer_name=("Customer Name", "first"),
            segment=("Segment", "first"),
            recency=("Order Date", lambda x: (ref_date - x.max()).days),
            frequency=("Order ID", "nunique"),
            monetary=("Sales", "sum"),
            profit=("Profit", "sum"),
            orders=("Order ID", "nunique"),
        )
        .reset_index()
    )
    return rfm


def segment_customers() -> dict:
    rfm = compute_rfm()

    features = rfm[["recency", "frequency", "monetary"]].copy()
    features["recency"] = features["recency"].clip(lower=1)
    features["monetary"] = features["monetary"].clip(lower=0)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(np.log1p(features))

    n_clusters = 4
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model.fit(scaled)
    rfm["cluster"] = model.labels_.tolist()

    profile = rfm.groupby("cluster").agg(
        count=("Customer ID", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_profit=("profit", "sum"),
    ).reset_index()

    centroids = scaler.inverse_transform(np.expm1(model.cluster_centers_))
    cluster_order = sorted(
        range(n_clusters),
        key=lambda c: centroids[c][1] * centroids[c][2] / (centroids[c][0] + 1),
        reverse=True,
    )

    labels = {
        0: "VIP",
        1: "Frecuentes",
        2: "Ocasionales",
        3: "Perdidos",
    }

    segments = []
    for rank, c in enumerate(cluster_order):
        row = profile[profile["cluster"] == c].iloc[0]
        segments.append({
            "cluster": int(c),
            "label": labels.get(rank, f"Cluster {c}"),
            "rank": rank + 1,
            "clientes": int(row["count"]),
            "avg_recency_dias": int(round(row["avg_recency"])),
            "avg_frequency": round(row["avg_frequency"], 1),
            "avg_monetary_usd": round(row["avg_monetary"], 2),
            "avg_monetary_fmt": f"${row['avg_monetary']:,.0f}",
            "total_profit": round(row["total_profit"], 2),
            "total_profit_fmt": f"${row['total_profit']:,.0f}",
        })

    scatter_data = []
    for _, row in rfm.iterrows():
        scatter_data.append({
            "customer": row["customer_name"],
            "segment": row["segment"],
            "recency": int(row["recency"]),
            "frequency": int(row["frequency"]),
            "monetary": round(row["monetary"], 2),
            "cluster": int(row["cluster"]),
            "cluster_label": next(s["label"] for s in segments if s["cluster"] == row["cluster"]),
        })

    return {"segments": segments, "scatter": scatter_data}
