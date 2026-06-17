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

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import (
    Flask, render_template, request, jsonify, send_from_directory,
)

from crawler import get_crawler, DEFAULT_SAVE_DIR
from report_manager import list_reports, count_unresolved, resolve_report, clear_resolved

app = Flask(__name__, template_folder=str(project_root / "templates"), static_folder=str(project_root / "static"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    keyword = data.get("keyword", "").strip()
    if not keyword:
        return jsonify({"error": "请输入书名"}), 400

    try:
        crawler = get_crawler()
        results = crawler.search(keyword)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json()
    book_id = data.get("book_id", "").strip()
    book_name = data.get("book_name", "未知").strip()
    author = data.get("author", "").strip() or "未知"
    thumb_url = data.get("thumb_url", "")
    abstract = data.get("abstract", "")

    if not book_id:
        return jsonify({"error": "缺少 book_id"}), 400

    crawler = get_crawler()

    # Generate task_id synchronously so frontend can poll immediately
    task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"

    def run_download():
        try:
            crawler.create_download_task(
                book_id, book_name,
                author=author,
                task_id=task_id,
            )
        except Exception as e:
            task = crawler._tasks.get(task_id)
            if task:
                task.status = "failed"

    thread = threading.Thread(target=run_download, daemon=True)
    thread.start()

    return jsonify({"task_id": task_id, "book_name": book_name})


@app.route("/api/progress/<task_id>", methods=["GET"])
def api_progress(task_id):
    crawler = get_crawler()
    progress = crawler.get_task_progress(task_id)
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
    crawler = get_crawler()
    history = crawler.get_history()
    return jsonify({"books": history})


@app.route("/api/open-folder", methods=["POST"])
def api_open_folder():
    folder = os.path.expanduser(DEFAULT_SAVE_DIR)
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
    host = "127.0.0.1"

    print(f"\n{'='*50}")
    print(f"  📚 番茄小说下载器")
    print(f"  服务地址: http://{host}:{port}")
    print(f"  按 Ctrl+C 停止服务")
    print(f"{'='*50}\n")

    webbrowser.open(f"http://{host}:{port}")

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
