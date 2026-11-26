"""Report generation for OSINT IG (JSON, CSV, HTML, and full case ZIP)."""
import csv
import html
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from typing import Optional

import httpx

from osint_ig.evidence import media_fetcher as download


def _fmt_ts(ts: Optional[int]) -> str:
    if not ts:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_json_report(run: dict) -> bytes:
    payload = {
        "platform": "OSINT IG",
        "title": "Instagram Intelligence Report",
        "prepared_by": "Mohsin Khawaja",
        "organization": "CSIB — Cyber Solutions & Information Board",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "investigation": {
            "id": run.get("id"),
            "target": run.get("target"),
            "target_id": run.get("target_id"),
            "backend": run.get("backend") or "instagrapi",
            "saved_at": run.get("saved_at"),
            "collected_at_utc": _fmt_ts(run.get("saved_at")),
            "api_calls_total": run.get("api_calls_total"),
            "modules": [r.get("name") for r in (run.get("results") or [])],
        },
        "results": run.get("results") or [],
        "ai_analysis": run.get("ai_analysis"),
        "limitations": (
            "Only publicly accessible data or data accessible to the authorized session is included. "
            "Private accounts, deleted content, and rate-limited endpoints may result in unavailable fields."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")


def build_csv_report(run: dict) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["target", "module", "status", "elapsed_ms", "record_index", "key_or_field", "value"])
    target = run.get("target") or ""
    for res in run.get("results") or []:
        mod = res.get("name") or ""
        status = "error" if res.get("is_error") else "ok"
        elapsed = res.get("elapsed_ms") or ""
        data = res.get("result")
        if isinstance(data, list):
            if not data:
                writer.writerow([target, mod, status, elapsed, 0, "empty", "[]"])
            for idx, item in enumerate(data, start=1):
                if isinstance(item, dict):
                    for k, v in item.items():
                        writer.writerow([target, mod, status, elapsed, idx, k, _cell(v)])
                else:
                    writer.writerow([target, mod, status, elapsed, idx, "value", _cell(item)])
        elif isinstance(data, dict):
            for k, v in data.items():
                if k in ("previews", "timestamps"):
                    continue
                writer.writerow([target, mod, status, elapsed, 1, k, _cell(v)])
        else:
            writer.writerow([target, mod, status, elapsed, 1, "value", _cell(data)])
    return buf.getvalue().encode("utf-8-sig")


def _cell(v) -> str:
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, default=str)
    return "" if v is None else str(v)


def _render_value_html(val) -> str:
    if val is None:
        return '<span class="muted">—</span>'
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if isinstance(val, (dict, list)):
        return f"<code>{html.escape(json.dumps(val, ensure_ascii=False, default=str))}</code>"
    s = str(val)
    if s.startswith(("http://", "https://")):
        esc_u = html.escape(s)
        return f'<a href="{esc_u}" target="_blank" rel="noopener">Open ↗</a>'
    return html.escape(s)


def _render_module_body(data) -> str:
    if isinstance(data, list):
        if not data:
            return '<p class="muted">No records returned.</p>'
        if isinstance(data[0], dict):
            cols = list(dict.fromkeys(k for row in data[:200] if isinstance(row, dict) for k in row.keys()))[:10]
            head = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
            rows_html = []
            for row in data[:200]:
                if not isinstance(row, dict):
                    continue
                tds = "".join(f"<td>{_render_value_html(row.get(c))}</td>" for c in cols)
                rows_html.append(f"<tr>{tds}</tr>")
            extra = f'<p class="muted">Showing first 200 of {len(data)} records (full dataset in CSV/JSON).</p>' if len(data) > 200 else ""
            return f'<div class="tbl-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>{extra}'
        items = "".join(f"<li>{_render_value_html(x)}</li>" for x in data[:200])
        return f"<ul>{items}</ul>"

    if isinstance(data, dict):
        rows = []
        for k, v in data.items():
            if k in ("previews", "timestamps"):
                continue
            rows.append(f"<tr><th>{html.escape(str(k))}</th><td>{_render_value_html(v)}</td></tr>")
        if rows:
            return f'<div class="tbl-wrap"><table class="kv-table"><tbody>{"".join(rows)}</tbody></table></div>'
    return f"<p>{_render_value_html(data)}</p>"


def build_html_report(run: dict) -> bytes:
    target = html.escape(str(run.get("target") or "Target-Free Search"))
    inv_id = html.escape(str(run.get("id") or "Unsaved Session"))
    collected_at = html.escape(_fmt_ts(run.get("saved_at")))
    backend = html.escape(str(run.get("backend") or "instagrapi"))
    api_calls = html.escape(str(run.get("api_calls_total") or 0))
    results = run.get("results") or []
    completed_count = sum(1 for r in results if not r.get("is_error"))
    error_count = sum(1 for r in results if r.get("is_error"))
    ai_analysis = run.get("ai_analysis")

    toc_links = []
    sections = []
    for idx, r in enumerate(results, start=1):
        name = html.escape(str(r.get("name") or "module"))
        anchor = f"mod-{idx}"
        status_cls = "err" if r.get("is_error") else "ok"
        status_txt = "Error" if r.get("is_error") else "Completed"
        elapsed = html.escape(str(r.get("elapsed_ms") or 0))
        toc_links.append(f'<a class="toc-pill" href="#{anchor}">{name}</a>')
        structured = _render_module_body(r.get("result"))
        raw = json.dumps(r.get("result"), ensure_ascii=False, indent=2, default=str)
        sections.append(
            f"""<section class="card" id="{anchor}">
  <div class="card-head">
    <h3>{idx}. {name}</h3>
    <span class="badge {status_cls}">{status_txt} · {elapsed} ms</span>
  </div>
  {structured}
  <details class="raw-details">
    <summary>Raw JSON Evidence</summary>
    <pre>{html.escape(raw)}</pre>
  </details>
</section>"""
        )

    ai_block = ""
    if ai_analysis:
        ai_block = f"""<section class="card ai-card">
  <div class="card-head">
    <h3>Gemini AI Post-Collection Analysis</h3>
    <span class="badge info">Optional Assistant</span>
  </div>
  <div class="ai-body">{html.escape(str(ai_analysis)).replace(chr(10), "<br>")}</div>
</section>"""

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>OSINT IG — Instagram Intelligence Report (@{target})</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #F8FAFC; color: #101828; margin: 0; padding: 32px; line-height: 1.5; }}
  .wrap {{ max-width: 1040px; margin: 0 auto; }}
  .header {{ background: #FFFFFF; border: 1px solid #E4E7EC; border-top: 4px solid #155EEF; border-radius: 8px; padding: 24px 28px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }}
  .brand {{ font-size: 12px; font-weight: 700; color: #155EEF; letter-spacing: 0.06em; text-transform: uppercase; }}
  h1 {{ margin: 4px 0 6px; font-size: 24px; color: #101828; }}
  .sub {{ color: #667085; font-size: 13px; margin: 0; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 18px; }}
  .kpi {{ background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px; padding: 14px 18px; }}
  .meta-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: #667085; font-weight: 600; }}
  .meta-val {{ font-size: 18px; font-weight: 700; color: #101828; margin-top: 4px; word-break: break-word; }}
  .toc {{ background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px; padding: 14px 18px; margin-bottom: 18px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
  .toc-pill {{ font-size: 12px; padding: 3px 10px; border-radius: 999px; background: #EFF6FF; color: #155EEF; text-decoration: none; font-weight: 500; }}
  .toc-pill:hover {{ background: #DBEAFE; }}
  .card {{ background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px; padding: 18px 22px; margin-bottom: 16px; }}
  .card-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #F2F4F7; padding-bottom: 10px; }}
  .card-head h3 {{ margin: 0; font-size: 15px; color: #101828; }}
  .badge {{ font-size: 12px; padding: 2px 10px; border-radius: 999px; font-weight: 600; }}
  .badge.ok {{ background: #ECFDF3; color: #027A48; }}
  .badge.err {{ background: #FEF3F2; color: #B42318; }}
  .badge.info {{ background: #EFF6FF; color: #155EEF; }}
  .tbl-wrap {{ overflow-x: auto; border: 1px solid #E4E7EC; border-radius: 6px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ padding: 8px 11px; text-align: left; border-bottom: 1px solid #E4E7EC; vertical-align: top; }}
  th {{ background: #F8FAFC; color: #475467; font-weight: 600; font-size: 12px; }}
  .kv-table th {{ width: 220px; }}
  tr:last-child td, tr:last-child th {{ border-bottom: none; }}
  a {{ color: #155EEF; text-decoration: none; font-weight: 500; }}
  a:hover {{ text-decoration: underline; }}
  .muted {{ color: #667085; font-size: 12px; }}
  .raw-details {{ margin-top: 10px; }}
  .raw-details summary {{ cursor: pointer; font-size: 12px; color: #667085; font-weight: 600; }}
  pre {{ background: #F8FAFC; border: 1px solid #E4E7EC; border-radius: 6px; padding: 12px; overflow-x: auto; font-size: 12px; max-height: 420px; margin-top: 8px; }}
  .ai-body {{ font-size: 14px; color: #101828; }}
  .footer {{ margin-top: 24px; font-size: 12px; color: #667085; border-top: 1px solid #E4E7EC; padding-top: 14px; }}
  @media print {{ body {{ background: #FFFFFF; padding: 0; }} .card, .header, .kpi {{ break-inside: avoid; }} .toc {{ display: none; }} }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div>
      <div class="brand">OSINT IG · Forensic Intelligence Report</div>
      <h1>@{target}</h1>
      <p class="sub">Prepared by: <strong>Mohsin Khawaja</strong> &nbsp;|&nbsp; Organization: <strong>CSIB — Cyber Solutions &amp; Information Board</strong></p>
    </div>
    <div style="text-align:right;font-size:12px;color:#667085;">
      <div><strong>Case ID:</strong> {inv_id}</div>
      <div><strong>Collected:</strong> {collected_at}</div>
      <div><strong>Provider:</strong> {backend}</div>
    </div>
  </div>
  <div class="kpi-grid">
    <div class="kpi"><div class="meta-label">Target Account</div><div class="meta-val">@{target}</div></div>
    <div class="kpi"><div class="meta-label">Modules Executed</div><div class="meta-val">{len(results)}</div></div>
    <div class="kpi"><div class="meta-label">Completed / Errors</div><div class="meta-val">{completed_count} / {error_count}</div></div>
    <div class="kpi"><div class="meta-label">Backend Requests</div><div class="meta-val">{api_calls}</div></div>
  </div>
  {f'<div class="toc"><span class="meta-label" style="margin-right:4px;">Modules:</span>{"".join(toc_links)}</div>' if toc_links else ''}
  {ai_block}
  {''.join(sections) if sections else '<div class="card">No module results recorded.</div>'}
  <div class="footer">
    <strong>Limitations &amp; Provenance:</strong> Data reflects only publicly available Instagram information or records accessible to the authorized session at collection time ({collected_at}). Private accounts or rate-limited endpoints may yield partial or unavailable fields.
  </div>
</div>
</body>
</html>"""
    return doc.encode("utf-8")


def _collect_media_urls(run: dict) -> list[str]:
    """Collect all downloadable Instagram CDN media URLs from run results."""
    urls: list[str] = []

    def _add(u):
        if isinstance(u, str) and download.is_allowed(u):
            urls.append(u)

    for res in run.get("results") or []:
        data = res.get("result")
        if isinstance(data, dict):
            _add(data.get("url"))
            _add(data.get("profile_pic_url"))
            for p in data.get("previews") or []:
                if isinstance(p, dict):
                    _add(p.get("media_url"))
                    _add(p.get("thumbnail_url"))
            for item in data.get("items") or []:
                if isinstance(item, dict):
                    _add(item.get("url") or item.get("media_url") or item.get("thumbnail_url"))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    _add(item)
                elif isinstance(item, dict):
                    _add(item.get("url") or item.get("media_url") or item.get("thumbnail_url") or item.get("cover_url"))
    return list(dict.fromkeys(urls))[: download.MAX_FILES]


def _write_list_csv(zf: zipfile.ZipFile, path: str, headers: list[str], rows: list[list]) -> None:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    zf.writestr(path, buf.getvalue().encode("utf-8-sig"))


def _write_extracted_lists(zf: zipfile.ZipFile, run: dict) -> None:
    """Write dedicated emails, phone numbers, followers, following, hashtags, and locations lists."""
    emails: list[tuple[str, str, str]] = []
    phones: list[tuple[str, str, str]] = []

    for res in run.get("results") or []:
        name = res.get("name") or ""
        data = res.get("result")
        if res.get("is_error") or data is None:
            continue

        if name == "get_user_info" and isinstance(data, dict):
            uname = str(data.get("username") or run.get("target") or "")
            if data.get("public_email"):
                emails.append((uname, str(data["public_email"]), "profile"))
            if data.get("contact_phone_number"):
                phones.append((uname, str(data["contact_phone_number"]), "profile"))

        elif name in ("get_followers_email", "get_followings_email") and isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("email"):
                    emails.append((str(item.get("username") or ""), str(item["email"]), name))

        elif name in ("get_followers_phone", "get_followings_phone") and isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("contact_phone_number"):
                    phones.append((str(item.get("username") or ""), str(item["contact_phone_number"]), name))

        elif name in ("get_followers", "get_followings") and isinstance(data, list):
            label = "followers" if name == "get_followers" else "following"
            rows = [[u.get("id", ""), u.get("username", ""), u.get("full_name", "")] for u in data if isinstance(u, dict)]
            _write_list_csv(zf, f"lists/{label}.csv", ["id", "username", "full_name"], rows)
            txt = "\n".join(str(u.get("username", "")) for u in data if isinstance(u, dict) and u.get("username"))
            zf.writestr(f"lists/{label}.txt", txt.encode("utf-8"))

        elif name == "get_hashtags" and isinstance(data, list):
            rows = [[h.get("hashtag", ""), h.get("count", 0)] for h in data if isinstance(h, dict)]
            _write_list_csv(zf, "lists/hashtags.csv", ["hashtag", "count"], rows)

        elif name == "get_addrs" and isinstance(data, list):
            rows = [
                [a.get("location_name") or a.get("name") or "", a.get("address", ""), a.get("lat", ""), a.get("lng", "")]
                for a in data
                if isinstance(a, dict)
            ]
            _write_list_csv(zf, "lists/locations.csv", ["location", "address", "lat", "lng"], rows)

        elif name == "get_captions" and isinstance(data, list):
            lines = [str(c.get("caption") or c) if isinstance(c, dict) else str(c) for c in data]
            zf.writestr("lists/captions.txt", "\n\n---\n\n".join(lines).encode("utf-8"))

    if emails:
        _write_list_csv(zf, "lists/emails.csv", ["username", "email", "source"], emails)
        zf.writestr("lists/emails.txt", "\n".join(f"{u}: {e}" for u, e, _ in emails).encode("utf-8"))
    if phones:
        _write_list_csv(zf, "lists/phone_numbers.csv", ["username", "phone_number", "source"], phones)
        zf.writestr("lists/phone_numbers.txt", "\n".join(f"{u}: {p}" for u, p, _ in phones).encode("utf-8"))


def _write_case_media(zf: zipfile.ZipFile, urls: list[str]) -> dict:
    """Download allowed Instagram CDN media into media/ inside the ZIP."""
    if not urls:
        return {"saved": 0, "failed": 0}
    used: set[str] = set()
    errors: list[str] = []
    saved = 0
    total = 0
    with httpx.Client(timeout=download.PER_FILE_TIMEOUT, follow_redirects=True) as client:
        for idx, url in enumerate(urls, start=1):
            if total >= download.MAX_TOTAL_BYTES:
                errors.append(f"{url} -> skipped (size limit)")
                continue
            try:
                resp = client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                errors.append(f"{url} -> {type(e).__name__}: {e}")
                continue
            content = resp.content
            total += len(content)
            saved += 1
            zf.writestr(f"media/{download._filename(url, idx, used)}", content)
    if errors:
        zf.writestr("media/errors.txt", "\n".join(errors).encode("utf-8"))
    return {"saved": saved, "failed": len(errors)}


def build_case_zip(run: dict) -> bytes:
    """Package the full investigation case (reports, lists, raw evidence, AI analysis, and media) into a ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("report.html", build_html_report(run))
        zf.writestr("report.json", build_json_report(run))
        zf.writestr("report.csv", build_csv_report(run))
        if run.get("ai_analysis"):
            zf.writestr("ai_analysis.md", str(run["ai_analysis"]).encode("utf-8"))
        for idx, res in enumerate(run.get("results") or [], start=1):
            mod = re.sub(r"[^A-Za-z0-9._-]+", "_", str(res.get("name") or f"module_{idx}"))
            zf.writestr(
                f"raw_evidence/{idx:02d}_{mod}.json",
                json.dumps(res, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
            )
        _write_extracted_lists(zf, run)
        media_stats = _write_case_media(zf, _collect_media_urls(run))
        manifest = {
            "platform": "OSINT IG",
            "prepared_by": "Mohsin Khawaja",
            "organization": "CSIB — Cyber Solutions & Information Board",
            "target": run.get("target"),
            "case_id": run.get("id"),
            "exported_at_utc": datetime.now(timezone.utc).isoformat(),
            "modules": [r.get("name") for r in (run.get("results") or [])],
            "includes_ai_analysis": bool(run.get("ai_analysis")),
            "media": media_stats,
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
    return buf.getvalue()
