import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

from ml import load_data


def get_rules(min_support: float = 0.008, min_lift: float = 1.0, top_n: int = 20) -> dict:
    df = load_data()

    basket = (
        df.groupby(["Order ID", "Sub-Category"])
        .size()
        .unstack(fill_value=0)
        .map(lambda x: 1 if x > 0 else 0)
    )
    basket = basket.astype(bool)

    frequent = apriori(basket, min_support=min_support, use_colnames=True)
    if frequent.empty:
        return {"rules": [], "total_rules": 0, "message": "No se encontraron reglas con los parámetros actuales."}

    rules = association_rules(frequent, metric="lift", min_threshold=min_lift)
    rules = rules.sort_values("lift", ascending=False).head(top_n)

    result = []
    for _, r in rules.iterrows():
        antecedents = ", ".join(sorted(r["antecedents"]))
        consequents = ", ".join(sorted(r["consequents"]))
        result.append({
            "antecedents": antecedents,
            "consequents": consequents,
            "support": round(r["support"] * 100, 2),
            "confidence": round(r["confidence"] * 100, 2),
            "lift": round(r["lift"], 2),
        })

    return {
        "rules": result,
        "total_rules": len(result),
        "params": {"min_support": min_support, "min_lift": min_lift},
    }
