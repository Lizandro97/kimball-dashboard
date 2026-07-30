import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.preprocessing import OneHotEncoder

from ml import load_data


def build_model():
    df = load_data()

    df["Month"] = df["Order Date"].dt.month.astype(str)

    cat_cols = ["Category", "Region", "Segment", "Ship Mode", "Month"]
    num_cols = ["Sales", "Discount", "Quantity"]

    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    encoded = encoder.fit_transform(df[cat_cols])
    encoded_df = pd.DataFrame(
        encoded, columns=encoder.get_feature_names_out(cat_cols), index=df.index
    )

    X = pd.concat([df[num_cols].reset_index(drop=True), encoded_df.reset_index(drop=True)], axis=1)
    y = df["Profit"].values

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)

    feature_names = num_cols + encoder.get_feature_names_out(cat_cols).tolist()
    importance = sorted(
        [
            {"feature": name, "coefficient": float(round(coef, 4))}
            for name, coef in zip(feature_names, model.coef_)
        ],
        key=lambda x: abs(x["coefficient"]),
        reverse=True,
    )

    return model, encoder, num_cols, cat_cols, float(r2), importance


_model = None
_encoder = None
_num_cols = None
_cat_cols = None
_r2 = None
_importance = None


def _ensure_model():
    global _model, _encoder, _num_cols, _cat_cols, _r2, _importance
    if _model is None:
        _model, _encoder, _num_cols, _cat_cols, _r2, _importance = build_model()


def predict(sales: float, discount: float, quantity: int,
            category: str, region: str, segment: str, ship_mode: str,
            month: int = 1) -> dict:
    _ensure_model()

    input_df = pd.DataFrame([{
        "Sales": sales,
        "Discount": discount,
        "Quantity": quantity,
        "Category": category,
        "Region": region,
        "Segment": segment,
        "Ship Mode": ship_mode,
        "Month": str(month),
    }])

    cat_df = pd.DataFrame(
        _encoder.transform(input_df[_cat_cols]),
        columns=_encoder.get_feature_names_out(_cat_cols),
        index=input_df.index,
    )
    X = pd.concat([input_df[_num_cols].reset_index(drop=True), cat_df.reset_index(drop=True)], axis=1)
    pred = _model.predict(X)[0]

    return {
        "predicted_profit": float(round(pred, 2)),
        "predicted_profit_fmt": f"${pred:,.2f}",
        "is_profitable": bool(pred > 0),
        "model_r2": float(round(_r2, 3)),
        "features": [{"feature": f["feature"], "importance": f["coefficient"]} for f in _importance[:10]],
    }


def model_info() -> dict:
    _ensure_model()
    return {
        "r2": float(round(_r2, 3)),
        "r2_pct": f"{_r2 * 100:.1f}%",
        "feature_importance": _importance[:10],
        "categories": sorted([str(c) for c in _encoder.categories_[0]]),
        "regions": sorted([str(c) for c in _encoder.categories_[1]]),
        "segments": sorted([str(c) for c in _encoder.categories_[2]]),
        "ship_modes": sorted([str(c) for c in _encoder.categories_[3]]),
        "months": [int(c) for c in sorted(_encoder.categories_[4], key=int)],
    }
