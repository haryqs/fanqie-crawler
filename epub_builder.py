"""
EPUB builder for Fanqie Novel crawler.
Generates clean EPUB v2/v3 with proper TOC, CSS, metadata.
"""

import time
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from io import BytesIO

import requests
from ebooklib import epub
from PIL import Image

logger = logging.getLogger(__name__)

CSS_STYLE = """
@namespace epub "http://www.idpf.org/2007/ops";
body {
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    line-height: 1.8;
    margin: 0;
    padding: 0.5em 1em;
    color: #222;
    background: #fff;
    text-rendering: optimizeLegibility;
}
h1 {
    font-size: 1.4em;
    font-weight: bold;
    text-align: center;
    margin: 1.5em 0 1em 0;
    padding-bottom: 0.5em;
    border-bottom: 1px solid #ddd;
    page-break-before: always;
}
h1:first-child {
    page-break-before: avoid;
}
p {
    text-indent: 2em;
    margin: 0.4em 0;
    text-align: justify;
    word-break: break-all;
    overflow-wrap: break-word;
}
.cover-page {
    text-align: center;
    padding-top: 20%;
}
.cover-page img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.toc-page h1 {
    border-bottom: none;
    page-break-before: avoid;
}
.toc-page ol {
    list-style: none;
    padding: 0;
    margin: 1em 0;
}
.toc-page li {
    padding: 0.3em 0;
    border-bottom: 1px dotted #ccc;
    font-size: 0.95em;
}
.meta-page {
    text-align: center;
    padding-top: 30%;
}
.meta-page h2 {
    font-size: 1.6em;
    margin-bottom: 0.5em;
}
.meta-page p {
    text-indent: 0;
    text-align: center;
    font-size: 0.9em;
    color: #666;
    margin: 0.3em 0;
}
"""


class EpubBuilder:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,*/*",
        })

    def build(
        self,
        title: str,
        author: str,
        description: str,
        chapters: List[Tuple[str, str]],
        cover_url: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        book = epub.EpubBook()

        book.set_identifier(f"fanqie-{hash(title)}-{int(time.time())}")
        book.set_title(title)
        book.set_language("zh-CN")
        book.add_author(author)
        book.add_metadata("DC", "description", description or "")
        book.add_metadata("DC", "publisher", "fanqie-crawler")
        book.add_metadata("DC", "date", time.strftime("%Y-%m-%d"))

        css = epub.EpubItem(
            uid="style",
            file_name="style/default.css",
            media_type="text/css",
            content=CSS_STYLE.encode("utf-8"),
        )
        book.add_item(css)

        spine = ["nav"]
        toc = []

        # Cover
        if cover_url:
            try:
                cover_img = self._download_cover(cover_url)
                if cover_img:
                    book.set_cover("cover.jpg", cover_img)

                    cover_page = epub.EpubHtml(
                        title="封面",
                        file_name="cover.xhtml",
                        lang="zh-CN",
                    )
                    cover_page.content = (
                        '<html xmlns="http://www.w3.org/1999/xhtml">'
                        "<head><link rel=\"stylesheet\" type=\"text/css\" href=\"style/default.css\"/></head>"
                        '<body><div class="cover-page">'
                        '<img src="cover.jpg" alt="Cover"/>'
                        "</div></body></html>"
                    )
                    cover_page.add_item(css)
                    book.add_item(cover_page)
                    spine.append(cover_page)
            except Exception:
                logger.warning("Failed to download cover image", exc_info=True)

        # Title page
        title_page = epub.EpubHtml(
            title="书籍信息",
            file_name="titlepage.xhtml",
            lang="zh-CN",
        )
        desc_lines = (description or "").replace("\n", "  \n")
        title_page.content = (
            '<html xmlns="http://www.w3.org/1999/xhtml">'
            "<head><link rel=\"stylesheet\" type=\"text/css\" href=\"style/default.css\"/></head>"
            '<body><div class="meta-page">'
            f"<h2>{self._escape_xml(title)}</h2>"
            f"<p>作者：{self._escape_xml(author)}</p>"
            f"<p>{self._escape_xml(desc_lines)}</p>"
            f"<p>下载时间：{time.strftime('%Y-%m-%d %H:%M')}</p>"
            "</div></body></html>"
        )
        title_page.add_item(css)
        book.add_item(title_page)
        spine.append(title_page)

        # TOC page
        toc_html = epub.EpubHtml(
            title="目录",
            file_name="toc.xhtml",
            lang="zh-CN",
        )
        toc_items = "".join(
            f"<li>{self._escape_xml(ch_title)}</li>"
            for ch_title, _ in chapters
        )
        toc_html.content = (
            '<html xmlns="http://www.w3.org/1999/xhtml">'
            "<head><link rel=\"stylesheet\" type=\"text/css\" href=\"style/default.css\"/></head>"
            '<body><div class="toc-page">'
            "<h1>目录</h1>"
            f"<ol>{toc_items}</ol>"
            "</div></body></html>"
        )
        toc_html.add_item(css)
        book.add_item(toc_html)
        spine.append(toc_html)

        # Chapters
        for idx, (ch_title, content) in enumerate(chapters):
            chapter = epub.EpubHtml(
                title=ch_title,
                file_name=f"chapter_{idx:05d}.xhtml",
                lang="zh-CN",
            )
            html_content = self._build_chapter_html(ch_title, content)
            chapter.content = html_content
            chapter.add_item(css)
            book.add_item(chapter)
            toc.append(chapter)
            spine.append(chapter)

        book.toc = toc
        book.spine = spine
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        if output_path is None:
            safe_name = self._sanitize_filename(title)
            output_path = Path(f"{safe_name}.epub")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(str(output_path), book, {})

        logger.info(f"EPUB written to: {output_path}")
        return output_path

    def _build_chapter_html(self, title: str, content: str) -> str:
        clean_title = self._escape_xml(title)
        paragraphs = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            safe_line = self._escape_xml(line)
            paragraphs.append(f"<p>{safe_line}</p>")

        body = "\n".join(paragraphs) if paragraphs else "<p>&#160;</p>"

        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<!DOCTYPE html>'
            '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">'
            "<head>"
            f"<title>{clean_title}</title>"
            '<link rel="stylesheet" type="text/css" href="style/default.css"/>'
            "</head>"
            "<body>"
            f"<h1>{clean_title}</h1>\n"
            f"{body}"
            "</body></html>"
        )

    def _download_cover(self, url: str) -> Optional[bytes]:
        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            img = img.convert("RGB")
            max_dim = 800
            if img.width > max_dim or img.height > max_dim:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=85, optimize=True)
            return buf.getvalue()
        except Exception:
            logger.debug("Cover download/conversion failed", exc_info=True)
            return None

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        illegal = '<>:"/\\|?*'
        result = []
        for ch in name:
            if ch in illegal:
                ch = {
                    "<": "＜", ">": "＞", ":": "：", '"': "＂",
                    "/": "／", "\\": "＼", "|": "｜", "?": "？",
                    "*": "＊",
                }.get(ch, "_")
            result.append(ch)
        return "".join(result).strip() or "unnamed"

    @staticmethod
    def _escape_xml(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
