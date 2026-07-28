"""Pydantic response models for API endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class KPIResponse(BaseModel):
    total_sales: float
    total_sales_fmt: str
    total_profit: float
    total_profit_fmt: str
    total_orders: int
    total_customers: int
    margin: float
    yoy_sales: float | None = None
    yoy_profit: float | None = None
    yoy_orders: float | None = None
    yoy_margin: float | None = None
    total_units: int = 0
    avg_qty_per_order: float = 0


class AlertResponse(BaseModel):
    discount_loss: float
    discount_loss_fmt: str
    south_margin: float
    tech_margin: float


class OverviewResponse(BaseModel):
    kpis: KPIResponse
    chart_monthly_trend: dict
    chart_region_donut: dict
    chart_category: dict
    top5_products: list[dict]
    alerts: AlertResponse


class TopProductItem(BaseModel):
    producto: str
    categoria: str
    subcategoria: str
    ventas: float
    ventas_fmt: str
    utilidad: float
    utilidad_fmt: str
    margen: float


class SalesResponse(BaseModel):
    chart_category: dict
    chart_region: dict
    chart_monthly: dict
    chart_subcategory: dict
    chart_map: dict
    top_products: list[TopProductItem]


class TierItem(BaseModel):
    nivel: str
    transacciones: int
    utilidad: float
    utilidad_fmt: str


class WinnerResponse(BaseModel):
    region: str
    category: str
    profit: str


class ProfitabilityResponse(BaseModel):
    discount_loss: float
    discount_loss_fmt: str
    discount_pct: float
    chart_discount: dict
    chart_region_category: dict
    tiers: list[TierItem]
    winner: WinnerResponse | None = None


class SegmentCard(BaseModel):
    segmento: str
    clientes: int
    ingresos: float
    ingresos_fmt: str
    ordenes: int
    avg_order: float
    avg_order_fmt: str
    margin: float
    avg_discount: float


class TopCustomer(BaseModel):
    rank: int
    name: str
    segment: str
    revenue: float
    revenue_fmt: str
    orders: int
    ticket: float
    ticket_fmt: str
    margin: float


class InsightResponse(BaseModel):
    top_segment: str
    top_ingresos: str
    avg_ticket: str
    total_customers: int
    repeat_rate: float


class CustomersResponse(BaseModel):
    chart_segment: dict
    chart_frequency: dict
    chart_segment_margin: dict
    segments: list[SegmentCard]
    top_customers: list[TopCustomer]
    insight: InsightResponse | None = None


class ShippingStats(BaseModel):
    avg_delivery_days: float
    on_time_pct: float
    total_orders: int
    by_mode: dict


class RegionKPI(BaseModel):
    region: str
    avg_days: float
    on_time_pct: float
    orders: int


class ShippingResponse(BaseModel):
    stats: ShippingStats
    region_kpis: list[RegionKPI]
    chart_by_region: dict
    chart_mode_impact: dict
    chart_histogram: dict


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    fact_rows: int | None = None
    last_etl_run: dict | None = None
    error: str | None = None


class FilterResponse(BaseModel):
    regions: list[str]
    years: list[str]
    segments: list[str]
