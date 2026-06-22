from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from crawler import CrawlerTask, DEFAULT_SAVE_DIR, FanqieCrawler
from epub_builder import EpubBuilder


class SourceError(RuntimeError):
    pass


class FanqieSource:
    source_id = "fanqie"
    name = "番茄小说"
    description = "内置番茄小说源，支持搜索、目录、章节下载和字体解码。"
    search_placeholder = "输入书名或作者..."

    def __init__(self, save_dir: Path = DEFAULT_SAVE_DIR):
        self._crawler = FanqieCrawler(save_dir=save_dir)

    def metadata(self) -> dict:
        return {
            "id": self.source_id,
            "name": self.name,
            "description": self.description,
            "search_placeholder": self.search_placeholder,
            "supports_search": True,
        }

    def search(self, keyword: str) -> list[dict]:
        results = self._crawler.search(keyword)
        for item in results:
            item["source_id"] = self.source_id
            item["source_name"] = self.name
        return results

    def create_download_task(
        self,
        book_id: str,
        book_name: str,
        author: str = "未知",
        task_id: Optional[str] = None,
        **_: object,
    ) -> CrawlerTask:
        return self._crawler.create_download_task(
            book_id=book_id,
            book_name=book_name,
            author=author,
            task_id=task_id,
        )

    def get_task_progress(self, task_id: str) -> Optional[dict]:
        progress = self._crawler.get_task_progress(task_id)
        if progress:
            progress["source_id"] = self.source_id
            progress["source_name"] = self.name
        return progress

    def get_history(self) -> list[dict]:
        books = self._crawler.get_history()
        filtered = []
        for book in books:
            meta_path = Path(book["file_path"]).with_suffix(".meta.json")
            source_id = ""
            if meta_path.exists():
                try:
                    source_id = json.loads(meta_path.read_text(encoding="utf-8")).get("source_id", "")
                except (json.JSONDecodeError, OSError):
                    source_id = ""
            if source_id and source_id != self.source_id:
                continue
            book["source_id"] = self.source_id
            book["source_name"] = self.name
            filtered.append(book)
        return filtered


class PublicWebSource:
    source_id = "web"
    name = "公开网页 URL"
    description = "把公开可访问的单页文章或章节保存为 EPUB；不绕过登录、付费墙、验证码或 DRM。"
    search_placeholder = "粘贴公开网页 URL..."
    _user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )

    def __init__(self, save_dir: Path = DEFAULT_SAVE_DIR):
        self._save_dir = Path(save_dir).expanduser().resolve()
        self._save_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self._user_agent})
        self._epub_builder = EpubBuilder()
        self._tasks: dict[str, CrawlerTask] = {}

    def metadata(self) -> dict:
        return {
            "id": self.source_id,
            "name": self.name,
            "description": self.description,
            "search_placeholder": self.search_placeholder,
            "supports_search": False,
        }

    def search(self, keyword: str) -> list[dict]:
        url = keyword.strip()
        if not self._is_http_url(url):
            return []
        title, author, abstract = self._preview(url)
        return [{
            "book_id": url,
            "book_name": title,
            "author": author,
            "word_count": 0,
            "status": "公开网页",
            "category": "网页",
            "abstract": abstract,
            "thumb_url": "",
            "source_id": self.source_id,
            "source_name": self.name,
        }]

    def create_download_task(
        self,
        book_id: str,
        book_name: str,
        author: str = "未知",
        task_id: Optional[str] = None,
        **_: object,
    ) -> CrawlerTask:
        task_id = task_id or f"task_{int(time.time())}"
        task = CrawlerTask(task_id, book_name or "公开网页", 1)
        self._tasks[task_id] = task

        try:
            task.status = "downloading"
            title, detected_author, content, description = self._extract_page(book_id)
            title = book_name if book_name and book_name != "未知" else title
            author = author if author and author != "未知" else detected_author
            output_path = self._save_dir / f"{self._sanitize_filename(title)}.epub"
            self._epub_builder.build(
                title=title,
                author=author or "未知",
                description=description,
                chapters=[("正文", content)],
                output_path=output_path,
            )
            meta_path = output_path.with_suffix(".meta.json")
            meta_path.write_text(
                json.dumps({
                    "title": title,
                    "author": author or "未知",
                    "source": self.name,
                    "source_id": self.source_id,
                    "url": book_id,
                    "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            task.completed = 1
            task.status = "completed"
            task.output_path = str(output_path)
            task.size_mb = round(output_path.stat().st_size / 1024 / 1024, 2)
        except Exception as exc:
            task.failed = 1
            task.status = "failed"
            task.errors.append(str(exc))
        return task

    def get_task_progress(self, task_id: str) -> Optional[dict]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {
            "task_id": task.task_id,
            "book_name": task.book_name,
            "status": task.status,
            "current_chapter": task.completed,
            "total_chapters": task.total_chapters,
            "completed": task.completed,
            "total": task.total_chapters,
            "failed": task.failed,
            "progress": round(task.completed / max(task.total_chapters, 1) * 100, 1),
            "errors": task.errors[:10],
            "output_path": task.output_path,
            "size_mb": task.size_mb,
            "source_id": self.source_id,
            "source_name": self.name,
        }

    def get_history(self) -> list[dict]:
        books = []
        for epub in sorted(self._save_dir.glob("*.epub"), key=lambda x: x.stat().st_mtime, reverse=True):
            meta_path = epub.with_suffix(".meta.json")
            source_id = ""
            source_name = ""
            author = "未知"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    source_id = meta.get("source_id", "")
                    source_name = meta.get("source", "")
                    author = meta.get("author", author)
                except (json.JSONDecodeError, OSError):
                    pass
            if source_id != self.source_id:
                continue
            books.append({
                "title": epub.stem,
                "author": author,
                "file_path": str(epub),
                "size_mb": round(epub.stat().st_size / 1024 / 1024, 2),
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(epub.stat().st_mtime)),
                "source_id": self.source_id,
                "source_name": self.name,
            })
        return books

    def _preview(self, url: str) -> tuple[str, str, str]:
        title, author, content, description = self._extract_page(url, preview=True)
        abstract = description or content[:160]
        return title, author, abstract

    def _extract_page(self, url: str, preview: bool = False) -> tuple[str, str, str, str]:
        if not self._is_http_url(url):
            raise SourceError("请输入 http 或 https 开头的公开网页 URL")
        if not self._robots_allowed(url):
            raise SourceError("该网站 robots.txt 不允许本工具抓取此 URL")

        resp = self._session.get(url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title = self._meta(soup, "og:title") or self._text(soup.find("h1")) or self._text(soup.find("title"))
        title = title or urlparse(url).netloc or "公开网页"
        author = (
            self._meta(soup, "author")
            or self._meta(soup, "article:author")
            or urlparse(url).netloc
            or "未知"
        )
        description = self._meta(soup, "description") or self._meta(soup, "og:description") or ""
        container = self._best_content_container(soup)
        content = self._content_text(container)
        if not content:
            raise SourceError("未能从该页面识别正文内容")
        if preview:
            content = content[:600]
        return title.strip(), author.strip(), content.strip(), description.strip()

    def _best_content_container(self, soup: BeautifulSoup):
        candidates = []
        selectors = [
            "article",
            "main",
            "[role='main']",
            ".chapter",
            ".content",
            ".article",
            ".post",
            ".entry-content",
            "#content",
            "#chaptercontent",
        ]
        for selector in selectors:
            candidates.extend(soup.select(selector))
        candidates.append(soup.body or soup)
        return max(candidates, key=lambda node: len(node.get_text("\n", strip=True)))

    def _content_text(self, node) -> str:
        paragraphs = [self._text(p) for p in node.find_all(["p", "section"])]
        paragraphs = [p for p in paragraphs if len(p) >= 8]
        if not paragraphs:
            text = node.get_text("\n", strip=True)
            paragraphs = [line.strip() for line in re.split(r"\n{1,}", text) if len(line.strip()) >= 8]
        return "\n".join(paragraphs)

    def _robots_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
            return parser.can_fetch(self._user_agent, url)
        except Exception:
            return True

    @staticmethod
    def _is_http_url(value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @staticmethod
    def _meta(soup: BeautifulSoup, name: str) -> str:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
        return tag.get("content", "").strip() if tag else ""

    @staticmethod
    def _text(node) -> str:
        return node.get_text(" ", strip=True) if node else ""

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        illegal = '<>:"/\\|?*'
        return "".join({"<": "＜", ">": "＞", ":": "：", '"': "＂", "/": "／", "\\": "＼", "|": "｜", "?": "？", "*": "＊"}.get(ch, ch) for ch in name).strip() or "unnamed"


class SourceManager:
    def __init__(self, save_dir: Path = DEFAULT_SAVE_DIR):
        self._save_dir = Path(save_dir).expanduser().resolve()
        self._sources = {
            FanqieSource.source_id: FanqieSource(save_dir=self._save_dir),
            PublicWebSource.source_id: PublicWebSource(save_dir=self._save_dir),
        }
        self._task_sources: dict[str, str] = {}
        self._lock = threading.Lock()

    @property
    def save_dir(self) -> Path:
        return self._save_dir

    def list_sources(self) -> list[dict]:
        return [source.metadata() for source in self._sources.values()]

    def get_source(self, source_id: str):
        source_id = source_id or FanqieSource.source_id
        if source_id not in self._sources:
            raise SourceError(f"未知源: {source_id}")
        return self._sources[source_id]

    def register_task(self, task_id: str, source_id: str) -> None:
        with self._lock:
            self._task_sources[task_id] = source_id

    def get_task_progress(self, task_id: str, source_id: str = "") -> Optional[dict]:
        source_ids = [source_id] if source_id else []
        if not source_ids:
            mapped = self._task_sources.get(task_id)
            if mapped:
                source_ids.append(mapped)
        if not source_ids:
            source_ids.extend(self._sources.keys())
        for sid in source_ids:
            source = self._sources.get(sid)
            if not source:
                continue
            progress = source.get_task_progress(task_id)
            if progress:
                return progress
        return None

    def get_history(self, source_id: str = "") -> list[dict]:
        sources = [self.get_source(source_id)] if source_id else self._sources.values()
        books = []
        for source in sources:
            books.extend(source.get_history())
        return sorted(books, key=lambda item: item.get("downloaded_at", ""), reverse=True)


SOURCE_MANAGER = SourceManager()
