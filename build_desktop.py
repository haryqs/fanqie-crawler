from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


APP_NAME = "NovelDownloader"


def data_arg(src: Path, dest: str) -> str:
    sep = ";" if os.name == "nt" else ":"
    return f"{src}{sep}{dest}"


def main() -> int:
    root = Path(__file__).resolve().parent
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        APP_NAME,
        "--add-data",
        data_arg(root / "templates", "templates"),
        "--add-data",
        data_arg(root / "static", "static"),
        "--hidden-import",
        "playwright.sync_api",
        "--hidden-import",
        "greenlet",
    ]

    playwright_dir = Path.home() / "AppData" / "Local" / "ms-playwright"
    if playwright_dir.exists():
        cmd.extend(["--add-data", data_arg(playwright_dir, "ms-playwright")])
    else:
        print("Playwright browser files were not found; run `python -m playwright install chromium` before building.")

    cmd.append(str(root / "app.py"))
    subprocess.check_call(cmd, cwd=root)
    print()
    print(f"Build complete: {root / 'dist' / APP_NAME}")
    print("Run NovelDownloader.exe inside that folder. EPUB files are saved to the exe folder's downloads directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
