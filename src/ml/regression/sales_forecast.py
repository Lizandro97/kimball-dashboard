import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml import load_data


def _build_features(monthly: pd.DataFrame, target: str):
    df = monthly[["date", target]].copy()
    df.columns = ["date", "value"]
    df["t"] = range(len(df))
    df["month"] = df["date"].dt.month
    df["lag_1"] = df["value"].shift(1).bfill()
    df["lag_12"] = df["value"].shift(12).bfill()
    df["ma_3"] = df["value"].rolling(3, min_periods=1).mean()
    return df


def _run_forecast(monthly: pd.DataFrame, target: str, months_ahead: int):
    df = _build_features(monthly, target)
    feature_cols = ["t", "month", "lag_1", "lag_12", "ma_3"]
    train = df.dropna().reset_index(drop=True)

    X = train[feature_cols]
    y = train["value"]
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    last_t = df["t"].iloc[-1]
    last_value = df["value"].values

    forecast_dates = pd.date_range(
        start=monthly["date"].max() + pd.DateOffset(months=1),
        periods=months_ahead,
        freq="ME",
    )

    points = []
    for i, fdate in enumerate(forecast_dates):
        t_val = last_t + i + 1
        month_val = fdate.month
        lag_1 = points[-1]["value"] if i > 0 else last_value[-1]
        lag_12_idx = len(last_value) - 12 + i
        lag_12 = last_value[lag_12_idx] if 0 <= lag_12_idx < len(last_value) else last_value.mean()
        recent = [p["value"] for p in points[-3:]] if points else last_value[-3:].tolist()
        ma_3 = np.mean(recent)

        features = pd.DataFrame([{
            "t": t_val, "month": month_val,
            "lag_1": lag_1, "lag_12": lag_12, "ma_3": ma_3,
        }])

        pred = model.predict(features)[0]
        points.append({
            "date": fdate,
            "value": round(max(pred, 0), 2) if target == "Sales" else round(pred, 2),
        })

    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    mape = np.mean(np.abs((y - y_pred) / np.where(np.abs(y) > 0.01, np.abs(y), 1))) * 100

    return {
        "points": points,
        "train_df": df,
        "metrics": {
            "mae": round(float(mae), 2),
            "mae_fmt": f"${mae:,.0f}",
            "rmse": round(float(rmse), 2),
            "rmse_fmt": f"${rmse:,.0f}",
            "mape": round(float(mape), 1),
            "mape_pct": f"{mape:.1f}%",
            "r2": round(float(r2), 3),
            "r2_pct": f"{r2 * 100:.1f}%",
        },
        "coefficients": {
            "t": round(float(model.coef_[0]), 2),
            "month": round(float(model.coef_[1]), 2),
            "lag_1": round(float(model.coef_[2]), 4),
            "lag_12": round(float(model.coef_[3]), 4),
            "ma_3": round(float(model.coef_[4]), 4),
        },
    }


def forecast_sales(months_ahead: int = 6) -> dict:
    df = load_data()

    monthly = (
        df.set_index("Order Date")
        .resample("ME")[["Sales", "Profit"]]
        .sum()
        .reset_index()
    )
    monthly.columns = ["date", "sales", "profit"]
    monthly = monthly.sort_values("date").reset_index(drop=True)

    sf = _run_forecast(monthly, "sales", months_ahead)
    pf = _run_forecast(monthly, "profit", months_ahead)

    historical = []
    for _, row in monthly.iterrows():
        historical.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "date_label": row["date"].strftime("%b %Y"),
            "sales": round(float(row["sales"]), 2),
            "sales_fmt": f"${row['sales']:,.0f}",
            "profit": round(float(row["profit"]), 2),
            "profit_fmt": f"${row['profit']:,.0f}",
            "is_forecast": False,
        })

    forecast = []
    for sp, pp in zip(sf["points"], pf["points"]):
        d = sp["date"]
        forecast.append({
            "date": d.strftime("%Y-%m-%d"),
            "date_label": d.strftime("%b %Y"),
            "sales": sp["value"],
            "sales_fmt": f"${sp['value']:,.0f}",
            "profit": pp["value"],
            "profit_fmt": f"${pp['value']:,.0f}",
            "is_forecast": True,
        })

    combined = historical + forecast

    return {
        "historical": combined,
        "forecast": forecast,
        "metrics": {
            "sales": sf["metrics"],
            "profit": pf["metrics"],
            "total_months": len(monthly),
            "forecast_months": months_ahead,
        },
        "coefficients": {
            "sales": sf["coefficients"],
            "profit": pf["coefficients"],
        },
    }
