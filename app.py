import json
import os
import random
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Windows console UTF-8 encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

project_root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
sys.path.insert(0, str(project_root))
bundled_playwright = project_root / "ms-playwright"
if bundled_playwright.exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(bundled_playwright))

from flask import (
    Flask, render_template, request, jsonify, send_from_directory,
)
from flask_cors import CORS

from crawler import DEFAULT_SAVE_DIR
from report_manager import list_reports, count_unresolved, resolve_report, clear_resolved
from sources import SOURCE_MANAGER, SourceError

app = Flask(__name__, template_folder=str(project_root / "templates"), static_folder=str(project_root / "static"))
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "endpoints": {
            "search": "POST /api/search",
            "download": "POST /api/download",
            "progress": "GET /api/progress/<task_id>",
            "history": "GET /api/history",
            "sources": "GET /api/sources",
        },
    })


@app.route("/api/sources", methods=["GET"])
def api_sources():
    return jsonify({
        "default_source": "fanqie",
        "sources": SOURCE_MANAGER.list_sources(),
    })


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json() or {}
    keyword = data.get("keyword", "").strip()
    source_id = data.get("source_id", "fanqie").strip() or "fanqie"
    if not keyword:
        return jsonify({"error": "请输入书名"}), 400

    try:
        source = SOURCE_MANAGER.get_source(source_id)
        results = source.search(keyword)
        return jsonify({"results": results, "source_id": source_id})
    except SourceError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json() or {}
    source_id = data.get("source_id", "fanqie").strip() or "fanqie"
    book_id = data.get("book_id", "").strip()
    book_name = data.get("book_name", "未知").strip()
    author = data.get("author", "").strip() or "未知"
    thumb_url = data.get("thumb_url", "")
    abstract = data.get("abstract", "")

    if not book_id:
        return jsonify({"error": "缺少 book_id"}), 400

    try:
        source = SOURCE_MANAGER.get_source(source_id)
    except SourceError as e:
        return jsonify({"error": str(e)}), 400

    # Generate task_id synchronously so frontend can poll immediately
    task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
    SOURCE_MANAGER.register_task(task_id, source_id)

    def run_download():
        try:
            source.create_download_task(
                book_id, book_name,
                author=author,
                task_id=task_id,
                thumb_url=thumb_url,
                abstract=abstract,
            )
        except Exception as e:
            task = getattr(source, "_tasks", {}).get(task_id)
            if task:
                task.status = "failed"
                task.errors.append(str(e))

    thread = threading.Thread(target=run_download, daemon=True)
    thread.start()

    return jsonify({"task_id": task_id, "book_name": book_name, "source_id": source_id})


@app.route("/api/progress/<task_id>", methods=["GET"])
def api_progress(task_id):
    source_id = request.args.get("source_id", "").strip()
    progress = SOURCE_MANAGER.get_task_progress(task_id, source_id=source_id)
    if progress is None:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(progress)


@app.route("/api/reports", methods=["GET"])
def api_reports():
    resolved = request.args.get("resolved")
    if resolved is not None:
        resolved = resolved.lower() == "true"

    reports = list_reports(resolved=resolved)
    return jsonify({
        "reports": reports,
        "unresolved_count": count_unresolved(),
    })


@app.route("/api/reports/<report_id>/resolve", methods=["POST"])
def api_resolve_report(report_id):
    data = request.get_json() or {}
    solution = data.get("solution", "")
    success = resolve_report(report_id, solution)
    return jsonify({"success": success})


@app.route("/api/reports/clear", methods=["POST"])
def api_clear_reports():
    clear_resolved()
    return jsonify({"success": True})


@app.route("/api/history", methods=["GET"])
def api_history():
    source_id = request.args.get("source_id", "").strip()
    history = SOURCE_MANAGER.get_history(source_id=source_id)
    return jsonify({"books": history})


@app.route("/api/open-folder", methods=["POST"])
def api_open_folder():
    folder = str(Path(DEFAULT_SAVE_DIR))
    try:
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        return jsonify({"success": True, "folder": folder})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def main():
    port = 5000
    host = "0.0.0.0"
    local_ip = "127.0.0.1"

    print(f"\n{'='*50}")
    print(f"  📚 番茄小说下载器")
    print(f"  本地访问: http://{local_ip}:{port}")
    print(f"  局域网访问: http://<本机IP>:{port}")
    print(f"  按 Ctrl+C 停止服务")
    print(f"{'='*50}\n")

    webbrowser.open(f"http://{local_ip}:{port}")

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
