from __future__ import annotations

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from ebooklib import epub


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
)

CSS = """
body {
    font-family: "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif CJK JP", serif;
    line-height: 1.9;
    margin: 0;
    padding: 1em;
    color: #222;
}
h1 {
    font-size: 1.35em;
    text-align: center;
    margin: 1.5em 0 1.2em;
    border-bottom: 1px solid #ddd;
    padding-bottom: .6em;
}
p {
    margin: .45em 0;
    text-indent: 1em;
}
.meta {
    text-align: center;
    padding-top: 25%;
}
.meta p {
    text-indent: 0;
}
.toc ol {
    padding-left: 1.5em;
}
.toc li {
    margin: .35em 0;
}
"""


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "ja,en;q=0.8,zh-CN;q=0.6",
    })
    return session


def get_soup(session: requests.Session, url: str, allow_404: bool = False) -> BeautifulSoup | None:
    for attempt in range(4):
        try:
            response = session.get(url, timeout=30)
            if allow_404 and response.status_code == 404:
                return None
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    return None


def text(node) -> str:
    return node.get_text("\n", strip=True) if node else ""


def escape_xml(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def clean_filename(name: str) -> str:
    return "".join("_" if ch in '<>:"/\\|?*' else ch for ch in name).strip() or "novel"


def ncode_from_url(url: str) -> str:
    match = re.search(r"/(n[0-9a-z]+)/?", urlparse(url).path, re.IGNORECASE)
    if not match:
        raise ValueError("Expected a Syosetu ncode URL such as https://ncode.syosetu.com/n2267be/")
    return match.group(1).lower()


def collect_index(session: requests.Session, base_url: str, ncode: str) -> tuple[str, str, str, list[dict]]:
    chapters: list[dict] = []
    title = author = description = ""
    page = 1

    while True:
        url = base_url if page == 1 else f"{base_url}?p={page}"
        soup = get_soup(session, url, allow_404=True)
        if soup is None:
            break

        if page == 1:
            title = text(soup.select_one("h1")) or (soup.title.string.strip() if soup.title else ncode)
            author = text(soup.select_one(".p-novel__author a")) or text(soup.select_one(".novel_writername a"))
            description_tag = soup.select_one('meta[property="og:description"]') or soup.select_one('meta[name="description"]')
            description = description_tag.get("content", "").strip() if description_tag else ""

        page_items = []
        chapter_pattern = re.compile(rf"/{re.escape(ncode)}/(\d+)/", re.IGNORECASE)
        for anchor in soup.select(".p-eplist__sublist a[href]"):
            href = anchor.get("href", "")
            match = chapter_pattern.fullmatch(href)
            if not match:
                continue
            page_items.append({
                "index": len(chapters) + len(page_items) + 1,
                "title": anchor.get_text(" ", strip=True),
                "url": urljoin(base_url, href),
            })

        if not page_items:
            break
        chapters.extend(page_items)
        print(f"Collected index page {page}: {len(page_items)} chapters, total {len(chapters)}", flush=True)
        page += 1
        time.sleep(0.25)

    return title, author or "Unknown", description, chapters


def fetch_chapter(session: requests.Session, chapter: dict) -> dict:
    soup = get_soup(session, chapter["url"])
    if soup is None:
        raise RuntimeError(f"Empty response for {chapter['url']}")

    title = text(soup.select_one(".p-novel__title")) or text(soup.select_one("h1")) or chapter["title"]
    body = first_non_empty_body(soup)
    if not body:
        raise RuntimeError(f"No body found for {chapter['url']}")

    paragraphs = [p.get_text("", strip=True) for p in body.select("p")]
    paragraphs = [p for p in paragraphs if p]
    if not paragraphs:
        paragraphs = [line.strip() for line in body.get_text("\n", strip=True).splitlines() if line.strip()]
    if not paragraphs:
        raise RuntimeError(f"Empty body for {chapter['url']}")

    return {
        "index": chapter["index"],
        "title": title,
        "url": chapter["url"],
        "content": "\n".join(paragraphs),
    }


def first_non_empty_body(soup: BeautifulSoup):
    candidates = []
    for selector in (
        ".js-novel-text",
        ".p-novel__text",
        ".p-novel__body",
        "#novel_honbun",
    ):
        candidates.extend(soup.select(selector))
    for candidate in candidates:
        if candidate.get_text("\n", strip=True):
            return candidate
    return candidates[0] if candidates else None


def load_or_fetch_chapter(cache_dir: Path, chapter: dict) -> dict:
    cache_path = cache_dir / f"{chapter['index']:04d}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    session = make_session()
    data = fetch_chapter(session, chapter)
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def chapter_html(title: str, content: str) -> str:
    paragraphs = "".join(f"<p>{escape_xml(line)}</p>" for line in content.split("\n") if line.strip())
    return (
        '<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><head>'
        f"<title>{escape_xml(title)}</title>"
        '<link rel="stylesheet" type="text/css" href="style/default.css"/>'
        f"</head><body><h1>{escape_xml(title)}</h1>{paragraphs or '<p>&#160;</p>'}</body></html>"
    )


def build_epub(output_path: Path, title: str, author: str, description: str, source_url: str, chapters: list[dict]) -> None:
    book = epub.EpubBook()
    book.set_identifier(f"syosetu-{ncode_from_url(source_url)}")
    book.set_title(title)
    book.set_language("ja")
    book.add_author(author)
    book.add_metadata("DC", "description", description)
    book.add_metadata("DC", "publisher", "fanqie-crawler")
    book.add_metadata("DC", "source", source_url)

    css = epub.EpubItem(uid="style", file_name="style/default.css", media_type="text/css", content=CSS.encode("utf-8"))
    book.add_item(css)

    spine = ["nav"]
    toc = []

    title_page = epub.EpubHtml(title="作品情報", file_name="titlepage.xhtml", lang="ja")
    title_page.content = (
        '<html xmlns="http://www.w3.org/1999/xhtml"><head>'
        '<link rel="stylesheet" type="text/css" href="style/default.css"/></head>'
        f'<body><div class="meta"><h1>{escape_xml(title)}</h1>'
        f"<p>{escape_xml(author)}</p><p>{escape_xml(source_url)}</p></div></body></html>"
    )
    title_page.add_item(css)
    book.add_item(title_page)
    spine.append(title_page)

    toc_page = epub.EpubHtml(title="目次", file_name="toc.xhtml", lang="ja")
    toc_items = "".join(f"<li>{escape_xml(chapter['title'])}</li>" for chapter in chapters)
    toc_page.content = (
        '<html xmlns="http://www.w3.org/1999/xhtml"><head>'
        '<link rel="stylesheet" type="text/css" href="style/default.css"/></head>'
        f'<body><div class="toc"><h1>目次</h1><ol>{toc_items}</ol></div></body></html>'
    )
    toc_page.add_item(css)
    book.add_item(toc_page)
    spine.append(toc_page)

    for chapter in chapters:
        item = epub.EpubHtml(
            title=chapter["title"],
            file_name=f"chapter_{chapter['index']:04d}.xhtml",
            lang="ja",
        )
        item.content = chapter_html(chapter["title"], chapter["content"])
        item.add_item(css)
        book.add_item(item)
        toc.append(item)
        spine.append(item)

    book.toc = toc
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book, {})


def main() -> int:
    parser = argparse.ArgumentParser(description="Download a public Syosetu novel to a local EPUB.")
    parser.add_argument("url")
    parser.add_argument("--output-dir", default="downloads")
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()

    base_url = args.url.rstrip("/") + "/"
    ncode = ncode_from_url(base_url)
    output_dir = Path(args.output_dir)
    cache_dir = output_dir / "_syosetu_cache" / ncode
    cache_dir.mkdir(parents=True, exist_ok=True)

    session = make_session()
    title, author, description, index = collect_index(session, base_url, ncode)
    if not index:
        raise RuntimeError("No chapters found")
    print(f"Book: {title} / {author} / {len(index)} chapters", flush=True)

    index_path = cache_dir / "index.json"
    index_path.write_text(
        json.dumps({"title": title, "author": author, "description": description, "chapters": index}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    results: dict[int, dict] = {}
    failures: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(args.workers, 1)) as pool:
        futures = {pool.submit(load_or_fetch_chapter, cache_dir, chapter): chapter for chapter in index}
        for done, future in enumerate(as_completed(futures), 1):
            chapter = futures[future]
            try:
                data = future.result()
                results[data["index"]] = data
            except Exception as exc:
                failures.append({**chapter, "error": str(exc)})
            if done % 25 == 0 or done == len(index):
                print(f"Downloaded {done}/{len(index)} chapters; failures={len(failures)}", flush=True)

    if failures:
        print("Retrying failures...", flush=True)
        retry_failures = []
        for chapter in failures:
            try:
                time.sleep(1)
                data = load_or_fetch_chapter(cache_dir, chapter)
                results[data["index"]] = data
            except Exception as exc:
                retry_failures.append({**chapter, "error": str(exc)})
        failures = retry_failures

    chapters = [results[item["index"]] for item in index if item["index"] in results]
    if not chapters:
        raise RuntimeError("No chapters downloaded")

    output_path = output_dir / f"{clean_filename(title)}.epub"
    build_epub(output_path, title, author, description, base_url, chapters)

    meta_path = output_path.with_suffix(".meta.json")
    meta_path.write_text(
        json.dumps({
            "title": title,
            "author": author,
            "source": "小説家になろう",
            "source_id": "syosetu",
            "url": base_url,
            "chapters_expected": len(index),
            "chapters_downloaded": len(chapters),
            "failures": failures,
            "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"EPUB: {output_path.resolve()}")
    print(f"META: {meta_path.resolve()}")
    print(f"Chapters downloaded: {len(chapters)}/{len(index)}")
    print(f"Size MB: {output_path.stat().st_size / 1024 / 1024:.2f}")
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
