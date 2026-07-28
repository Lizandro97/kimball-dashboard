"""Export routes — multi-sheet Excel per module + legacy CSV."""

import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.services.chart_service import filter_data, load_data
from api.services.export_service import EXPORT_BUILDERS

router = APIRouter()


@router.get("/export/csv")
def export_csv(
    region: str = Query("Todas"),
    year: str = Query("Todos"),
    segment: str = Query("Todos"),
):
    df = filter_data(load_data(), region, year, segment)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(df.columns.tolist())
    for _, r in df.iterrows():
        w.writerow(r.tolist())
    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=superstore_export.csv"},
    )


@router.get("/export/{module}")
def export_module(
    module: str,
    region: str = Query("Todas"),
    year: str = Query("Todos"),
    segment: str = Query("Todos"),
):
    if module not in EXPORT_BUILDERS:
        raise HTTPException(status_code=404, detail=f"Modulo '{module}' no encontrado")

    buf = EXPORT_BUILDERS[module](region, year, segment)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=superstore_{module}.xlsx"
        },
    )