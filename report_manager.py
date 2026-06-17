import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

REPORTS_DIR = Path(__file__).parent / "reports"


def _ensure_dir():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ReportLevel:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReportType:
    RATE_LIMIT = "rate_limit"
    AUTH_FAILURE = "auth_failure"
    CONTENT_DECRYPT = "content_decrypt"
    CHAPTER_MISSING = "chapter_missing"
    NETWORK_ERROR = "network_error"
    API_CHANGED = "api_changed"
    CAPTCHA = "captcha"
    UNKNOWN = "unknown"


def create_report(
    report_type: str,
    message: str,
    level: str = ReportLevel.WARNING,
    context: dict = None,
    resolved: bool = False,
) -> str:
    _ensure_dir()

    report_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now().isoformat()
    unix_ts = time.time()

    report = {
        "id": report_id,
        "timestamp": timestamp,
        "unix_ts": unix_ts,
        "type": report_type,
        "level": level,
        "message": message,
        "context": context or {},
        "resolved": resolved,
        "resolved_at": None,
        "solution": None,
    }

    filepath = REPORTS_DIR / f"{report_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_id


def resolve_report(report_id: str, solution: str = ""):
    filepath = REPORTS_DIR / f"{report_id}.json"
    if not filepath.exists():
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        report = json.load(f)

    report["resolved"] = True
    report["resolved_at"] = datetime.now().isoformat()
    report["solution"] = solution

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return True


def list_reports(resolved: Optional[bool] = None, limit: int = 50) -> list:
    _ensure_dir()
    reports = []

    for f in sorted(REPORTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                r = json.load(fh)
            if resolved is None or r.get("resolved") == resolved:
                reports.append(r)
        except (json.JSONDecodeError, KeyError):
            pass
        if len(reports) >= limit:
            break

    return reports


def count_unresolved() -> int:
    return len(list_reports(resolved=False))


def latest_report() -> Optional[dict]:
    reports = list_reports(limit=1)
    return reports[0] if reports else None


def clear_resolved():
    _ensure_dir()
    for f in REPORTS_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                r = json.load(fh)
            if r.get("resolved"):
                f.unlink()
        except (json.JSONDecodeError, KeyError):
            f.unlink()
