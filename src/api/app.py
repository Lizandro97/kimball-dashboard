"""FastAPI BI Dashboard — sirve datos + static/."""

from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from api.error_handlers import register_error_handlers
from api.routes import customers, export, overview, profitability, sales, shipping
from api.services.chart_service import load_data
from core.config import settings
from db.engine import get_engine
from db.models import EtlLog, FSales

app = FastAPI(title=settings.APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(overview.router, prefix="/api")
app.include_router(sales.router, prefix="/api")
app.include_router(profitability.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(shipping.router, prefix="/api")
app.include_router(export.router, prefix="/api")


@app.get("/api/health")
def health_check():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            fact_count = conn.execute(select(func.count()).select_from(FSales)).scalar()
            last_etl_row = conn.execute(
                select(EtlLog.log_id, EtlLog.step, EtlLog.run_date, EtlLog.status)
                .order_by(EtlLog.log_id.desc())
                .limit(1)
            ).mappings().first()
            last_etl = dict(last_etl_row) if last_etl_row else None
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "fact_rows": fact_count,
            "last_etl_run": last_etl,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e),
        }


@app.get("/api/filters")
def get_filters():
    df = load_data()
    return {
        "regions": ["Todas"] + sorted(df["region"].unique().tolist()),
        "years": ["Todos"] + sorted(df["order_date"].dt.year.unique().astype(str).tolist()),
        "segments": ["Todos"] + sorted(df["segment"].unique().tolist()),
        "total_fact_rows": int(len(df)),
    }


static_dir = Path(__file__).parent.parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
