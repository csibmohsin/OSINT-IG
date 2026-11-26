"""Media ZIP download and multi-format forensic report export routes."""
import json
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from osint_ig.api.schemas import DownloadRequest, ReportExportRequest
from osint_ig.api.security import require_local_origin
from osint_ig.evidence import exporter, media_fetcher

router = APIRouter()


@router.post("/api/download")
def download_media(req: DownloadRequest):
    try:
        content, report = media_fetcher.build_zip(req.urls)
    except media_fetcher.DownloadError as exc:
        raise HTTPException(400, str(exc)) from exc
    filename = f"osint_ig_{re.sub(r'[^A-Za-z0-9._-]+', '_', req.name)[:60] or 'media'}.zip"
    return Response(
        content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Download-Report": json.dumps(report),
            "Access-Control-Expose-Headers": "X-Download-Report",
        },
    )


@router.post("/api/report/export")
def export_report(req: ReportExportRequest, request: Request):
    require_local_origin(request)
    fmt = (req.format or "html").lower().strip()
    target_slug = re.sub(r"[^A-Za-z0-9._-]+", "_", str(req.run.get("target") or "investigation"))[:50]
    if fmt == "json":
        content = exporter.build_json_report(req.run)
        media_type, ext = "application/json", "json"
    elif fmt == "csv":
        content = exporter.build_csv_report(req.run)
        media_type, ext = "text/csv; charset=utf-8", "csv"
    elif fmt == "html":
        content = exporter.build_html_report(req.run)
        media_type, ext = "text/html; charset=utf-8", "html"
    elif fmt == "zip":
        content = exporter.build_case_zip(req.run)
        media_type, ext = "application/zip", "zip"
    else:
        raise HTTPException(400, f"Unsupported export format: {fmt}")
    prefix = "osint_ig_case_" if fmt == "zip" else "osint_ig_report_"
    filename = f"{prefix}{target_slug}.{ext}"
    return Response(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
