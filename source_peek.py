"""
Educational source peek — map UI pieces to project files + code blocks.

Students can click a </> button on charts/filters to see where that feature
lives in Python (and related JS). Toggle visibility in Settings.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

from charts import reports

ROOT = Path(__file__).resolve().parent
COOKIE_SHOW_SOURCE = "postal_show_source"


def _rel(path: Path | str) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _from_callable(fn, note: str = "") -> dict:
    src = inspect.getsource(fn)
    lines, start = inspect.getsourcelines(fn)
    end = start + len(lines) - 1
    path = _rel(inspect.getsourcefile(fn))
    return {
        "path": path,
        "start_line": start,
        "end_line": end,
        "note": note or f"function `{fn.__name__}`",
        "code": src.rstrip() + "\n",
    }


def _from_file_range(rel_path: str, start: int, end: int, note: str = "") -> dict:
    path = ROOT / rel_path
    all_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start = max(1, start)
    end = min(len(all_lines), end)
    code = "".join(all_lines[start - 1 : end])
    return {
        "path": rel_path.replace("\\", "/"),
        "start_line": start,
        "end_line": end,
        "note": note,
        "code": code,
    }


def _find_py_def(rel_path: str, def_name: str, note: str = "") -> dict | None:
    """Find a top-level or indented `def name(` block by brace-less indent matching."""
    path = ROOT / rel_path
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    pattern = re.compile(rf"^(\s*)def\s+{re.escape(def_name)}\s*\(")
    start_i = None
    base_indent = ""
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            start_i = i
            base_indent = m.group(1)
            break
    if start_i is None:
        return None

    end_i = start_i
    for j in range(start_i + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            end_i = j
            continue
        # Still part of function if indented more than def line
        if line.startswith(base_indent) and (
            len(line) > len(base_indent) and line[len(base_indent)] in (" ", "\t")
        ):
            end_i = j
            continue
        # Decorators / next sibling at same indent → stop
        break

    start_line = start_i + 1
    end_line = end_i + 1
    code = "".join(lines[start_i : end_i + 1])
    return {
        "path": rel_path.replace("\\", "/"),
        "start_line": start_line,
        "end_line": end_line,
        "note": note or f"def `{def_name}`",
        "code": code.rstrip() + "\n",
    }


def _find_js_fn(rel_path: str, fn_name: str, note: str = "") -> dict | None:
    """Grab a JS function block by name (best-effort brace match)."""
    path = ROOT / rel_path
    text = path.read_text(encoding="utf-8")
    patterns = [
        rf"function\s+{re.escape(fn_name)}\s*\(",
        rf"(?:const|let|var)\s+{re.escape(fn_name)}\s*=\s*(?:async\s*)?function\s*\(",
        rf"(?:const|let|var)\s+{re.escape(fn_name)}\s*=\s*(?:async\s*)?\(",
    ]
    match = None
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            break
    if not match:
        return None

    start_idx = match.start()
    brace_at = text.find("{", match.end() - 1)
    if brace_at < 0:
        return None
    depth = 0
    end_idx = brace_at
    for i in range(brace_at, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_idx = i + 1
                break
    snippet = text[start_idx:end_idx]
    start_line = text.count("\n", 0, start_idx) + 1
    end_line = text.count("\n", 0, end_idx) + 1
    return {
        "path": rel_path.replace("\\", "/"),
        "start_line": start_line,
        "end_line": end_line,
        "note": note or f"JS `{fn_name}`",
        "code": snippet.rstrip() + "\n",
    }


def _catalog() -> dict:
    """Keys used by data-source-key / API. Built at call time so lines stay correct."""
    entries = {
        "dashboard.filters": {
            "title": "Dashboard filters",
            "parts": [
                _from_callable(reports.resolve_date_range, "Date presets / range"),
                _from_callable(reports._filtered_orders, "Apply filters to Order query"),
                _find_js_fn("static/js/dashboard.js", "collectFilters", "JS: collect filter values"),
                _find_js_fn("static/js/dashboard.js", "loadReport", "JS: reload report with filters"),
            ],
        },
        "dashboard.presets": {
            "title": "Date preset buttons",
            "parts": [
                _from_callable(reports.resolve_date_range, "today / week / month / year windows"),
                _find_js_fn("static/js/dashboard.js", "setActivePreset", "JS: preset button state"),
            ],
        },
        "dashboard.reports_ui": {
            "title": "Report buttons (UI)",
            "parts": [
                _from_callable(reports.get_report_catalog, "Report catalog labels"),
                _find_js_fn("static/js/dashboard.js", "setActiveReport", "JS: active report button"),
                _find_js_fn("static/js/dashboard.js", "loadReport", "JS: fetch /api/report/<key>"),
            ],
        },
        "dashboard.stats": {
            "title": "Dashboard stat cards",
            "parts": [
                _find_py_def("app.py", "dashboard", "Route `/` - computes stats for the top cards"),
            ],
        },
        "api.report": {
            "title": "Report API endpoint",
            "parts": [
                _find_py_def("app.py", "api_report", "Route `/api/report/<report_key>`"),
                _from_callable(reports.build_report, "Dispatches to the right builder"),
            ],
        },
        "report.orders": {
            "title": "Orders Report",
            "parts": [
                _from_callable(reports.build_orders_report, "Builds all Orders report charts"),
                _from_callable(reports._filtered_orders, "Shared filter query"),
                _from_callable(reports._bar, "Bar chart helper"),
                _from_callable(reports._pie, "Pie / donut helper"),
                _from_callable(reports._line, "Line chart helper"),
            ],
        },
        "report.revenue": {
            "title": "Revenue Report",
            "parts": [
                _from_callable(reports.build_revenue_report, "Builds Revenue report charts"),
                _from_callable(reports._filtered_orders, "Shared filter query"),
            ],
        },
        "report.delivery": {
            "title": "Delivery Report",
            "parts": [
                _from_callable(reports.build_delivery_report, "Builds Delivery report charts"),
            ],
        },
        "report.inventory": {
            "title": "Inventory Report",
            "parts": [
                _from_callable(reports.build_inventory_report, "Builds Inventory / sales charts"),
            ],
        },
        "report.ratings": {
            "title": "Ratings Report",
            "parts": [
                _from_callable(reports.build_ratings_report, "Builds Ratings report charts"),
            ],
        },
        "report.correlations": {
            "title": "Heatmap / Correlations Report",
            "parts": [
                _from_callable(reports.build_correlations_report, "Heatmaps + price vs rating"),
            ],
        },
        "chart.helpers": {
            "title": "Chart drawing helpers (Matplotlib)",
            "parts": [
                _from_callable(reports._bar, "`_bar` — bar / horizontal bar"),
                _from_callable(reports._pie, "`_pie` — pie / donut"),
                _from_callable(reports._line, "`_line` — line / area"),
                _from_callable(reports._to_base64, "PNG → base64 for the browser"),
            ],
        },
    }
    for entry in entries.values():
        entry["parts"] = [p for p in entry["parts"] if p]
    return entries


def list_source_keys() -> list[str]:
    return sorted(_catalog().keys())


def get_source(key: str) -> dict | None:
    entry = _catalog().get(key)
    if not entry:
        return None
    return {
        "key": key,
        "title": entry["title"],
        "parts": entry["parts"],
    }


def report_source_key(report_key: str) -> str:
    return f"report.{report_key}"


def show_source_enabled() -> bool:
    from flask import g

    return bool(getattr(g, "show_source", False))


def resolve_show_source():
    """Read toggle into flask.g (call from before_request)."""
    from flask import g, request, session

    raw = request.cookies.get(COOKIE_SHOW_SOURCE)
    if raw is None:
        raw = session.get("show_source")
    # Default ON so students see the teaching buttons
    if raw is None:
        enabled = True
    else:
        enabled = str(raw).lower() in {"1", "true", "on", "yes"}
    g.show_source = enabled
