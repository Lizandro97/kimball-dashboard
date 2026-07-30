from fastapi import APIRouter, Query

from ml.clustering.rfm import segment_customers
from ml.clustering.product_clusters import segment_products
from ml.clustering.profit_segments import segment_profitability
from ml.association.market_basket import get_rules
from ml.regression.sales_forecast import forecast_sales
from ml.regression.profit_predictor import predict, model_info

router = APIRouter()


@router.get("/ml/rfm")
def get_rfm():
    return segment_customers()


@router.get("/ml/products")
def get_ml_products():
    return segment_products()


@router.get("/ml/profit-segments")
def get_profit_segments():
    return segment_profitability()


@router.get("/ml/basket")
def get_basket(
    min_support: float = Query(0.008, ge=0.001, le=0.5),
    min_lift: float = Query(1.0, ge=1.0, le=10.0),
):
    return get_rules(min_support=min_support, min_lift=min_lift)


@router.get("/ml/forecast")
def get_forecast(months_ahead: int = Query(6, ge=1, le=24)):
    return forecast_sales(months_ahead=months_ahead)


@router.get("/ml/profit-predict")
def get_profit_predict(
    sales: float = Query(500, ge=0, le=10000),
    discount: float = Query(0.1, ge=0, le=0.8),
    quantity: int = Query(2, ge=1, le=50),
    category: str = Query("Technology"),
    region: str = Query("West"),
    segment: str = Query("Consumer"),
    ship_mode: str = Query("Standard Class"),
    month: int = Query(7, ge=1, le=12),
):
    return predict(sales, discount, quantity, category, region, segment, ship_mode, month=month)


@router.get("/ml/profit-predict/info")
def get_profit_predict_info():
    return model_info()
