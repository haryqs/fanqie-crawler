import json
import logging
import os
import queue
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from epub_builder import EpubBuilder
from report_manager import create_report, ReportType, ReportLevel

logger = logging.getLogger("fanqie.crawler")

DEFAULT_SAVE_DIR = os.path.expanduser("~/Documents/番茄小说")
MAX_RETRIES = 3
BASE_DELAY = 0.5
MAX_WORKERS = 8

SEARCH_API = "https://fanqienovel.com/api/author/search/search_book/v1"
DIRECTORY_API = "https://fanqienovel.com/api/reader/directory/detail"
CHAPTER_API = "https://fanqienovel.com/api/reader/full"
CHAPTER_API_MOBILE = "https://novel.snssdk.com/api/novel/book/reader/full/v1"
PAGE_URL = "https://fanqienovel.com/page/{book_id}"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

CODE_MAP = [[58344, 58715], [58345, 58716]]
CHARSET = [
    ["D","在","主","特","家","军","然","表","场","4","要","只","v","和","?","6","别","还","g","现","儿","岁","?","?","此","象","月","3","出","战","工","相","o","男","直","失","世","F","都","平","文","什","V","O","将","真","T","那","当","?","会","立","些","u","是","十","张","学","气","大","爱","两","命","全","后","东","性","通","被","1","它","乐","接","而","感","车","山","公","了","常","以","何","可","话","先","p","i","叫","轻","M","士","w","着","变","尔","快","l","个","说","少","色","里","安","花","远","7","难","师","放","t","报","认","面","道","S","?","克","地","度","I","好","机","U","民","写","把","万","同","水","新","没","书","电","吃","像","斯","5","为","y","白","几","日","教","看","但","第","加","候","作","上","拉","住","有","法","r","事","应","位","利","你","声","身","国","问","马","女","他","Y","比","父","x","A","H","N","s","X","边","美","对","所","金","活","回","意","到","z","从","j","知","又","内","因","点","Q","三","定","8","R","b","正","或","夫","向","德","听","更","?","得","告","并","本","q","过","记","L","让","打","f","人","就","者","去","原","满","体","做","经","K","走","如","孩","c","G","给","使","物","?","最","笑","部","?","员","等","受","k","行","一","条","果","动","光","门","头","见","往","自","解","成","处","天","能","于","名","其","发","总","母","的","死","手","入","路","进","心","来","h","时","力","多","开","已","许","d","至","由","很","界","n","小","与","Z","想","代","么","分","生","口","再","妈","望","次","西","风","种","带","J","?","实","情","才","这","?","E","我","神","格","长","觉","间","年","眼","无","不","亲","关","结","0","友","信","下","却","重","己","老","2","音","字","m","呢","明","之","前","高","P","B","目","太","e","9","起","稜","她","也","W","用","方","子","英","每","理","便","四","数","期","中","C","外","样","a","海","们","任"],
    ["s","?","作","口","在","他","能","并","B","士","4","U","克","才","正","们","字","声","高","全","尔","活","者","动","其","主","报","多","望","放","h","w","次","年","?","中","3","特","于","十","入","要","男","同","G","面","分","方","K","什","再","教","本","己","结","1","等","世","N","?","说","g","u","期","Z","外","美","M","行","给","9","文","将","两","许","张","友","0","英","应","向","像","此","白","安","少","何","打","气","常","定","间","花","见","孩","它","直","风","数","使","道","第","水","已","女","山","解","d","P","的","通","关","性","叫","儿","L","妈","问","回","神","来","S","","四","望","前","国","些","O","v","l","A","心","平","自","无","军","光","代","是","好","却","c","得","种","就","意","先","立","z","子","过","Y","j","表","","么","所","接","了","名","金","受","J","满","眼","没","部","那","m","每","车","度","可","R","斯","经","现","门","明","V","如","走","命","y","6","E","战","很","上","f","月","西","7","长","夫","想","话","变","海","机","x","到","W","一","成","生","信","笑","但","父","开","内","东","马","日","小","而","后","带","以","三","几","为","认","X","死","员","目","位","之","学","远","人","音","呢","我","q","乐","象","重","对","个","被","别","F","也","书","稜","D","写","还","因","家","发","时","i","或","住","德","当","o","l","比","觉","然","吃","去","公","a","老","亲","情","体","太","b","万","C","电","理","?","失","力","更","拉","物","着","原","她","工","实","色","感","记","看","出","相","路","大","你","候","2","和","?","与","p","样","新","只","便","最","不","进","T","r","做","格","母","总","爱","身","师","轻","知","往","加","从","?","天","e","H","?","听","场","由","快","边","让","把","任","8","条","头","事","至","起","点","真","手","这","难","都","界","用","法","n","处","下","又","Q","告","地","5","k","t","岁","有","会","果","利","民"],
]


class CrawlerTask:
    def __init__(self, task_id: str, book_name: str, total_chapters: int):
        self.task_id = task_id
        self.book_name = book_name
        self.total_chapters = total_chapters
        self.completed = 0
        self.failed = 0
        self.errors = []
        self.status = "preparing"
        self.output_path = None
        self.size_mb = 0
        self.error_report_ids = []


class FanqieCrawler:
    def __init__(self, save_dir: str = DEFAULT_SAVE_DIR, max_workers: int = MAX_WORKERS):
        self._save_dir = Path(save_dir).expanduser().resolve()
        self._save_dir.mkdir(parents=True, exist_ok=True)
        self._max_workers = max_workers
        self._session = requests.Session()
        self._cookie = self._generate_cookie()
        self._epub_builder = EpubBuilder()
        self._tasks: dict[str, CrawlerTask] = {}
        # Thread-safe browser: dedicated thread with request queue
        self._browser_queue = queue.Queue()
        self._browser_ready = threading.Event()
        self._browser_error = None
        self._browser_thread = threading.Thread(target=self._browser_worker, daemon=True, name="fanqie-browser")
        self._browser_thread.start()
        # Wait for browser to be ready (with timeout)
        if not self._browser_ready.wait(timeout=45):
            raise RuntimeError("Browser failed to initialize within timeout")

    def _browser_worker(self):
        """Runs in dedicated thread. All Playwright operations happen here."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self._browser_error = "Playwright not installed."
            self._browser_ready.set()
            return

        pw = None
        browser = None
        page = None
        try:
            pw = sync_playwright().start()
            browser = pw.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                locale="zh-CN",
            )
            page = context.new_page()
            page.goto("https://fanqienovel.com/", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            logger.info("Browser worker ready")
            self._browser_ready.set()

            # Process API call requests
            while True:
                try:
                    task = self._browser_queue.get(timeout=5)
                    if task is None:  # Shutdown signal
                        break
                    req_id, url, params, result_queue = task
                    try:
                        full_url = url
                        if params:
                            full_url = url + "?" + urlencode(params, safe="%")
                        full_url_escaped = full_url.replace("\\", "\\\\").replace("'", "\\'")
                        js_code = f"""
                        async () => {{
                            const resp = await fetch('{full_url_escaped}', {{
                                headers: {{'Accept': 'application/json'}},
                                credentials: 'include',
                            }});
                            if (!resp.ok) {{
                                throw new Error('HTTP ' + resp.status);
                            }}
                            const text = await resp.text();
                            try {{
                                return JSON.parse(text);
                            }} catch(e) {{
                                return {{_raw: text, _error: 'JSON parse failed'}};
                            }}
                        }}
                        """
                        result = page.evaluate(js_code)
                        result_queue.put((req_id, result, None))
                    except Exception as e:
                        result_queue.put((req_id, None, str(e)))
                except queue.Empty:
                    continue
        except Exception as e:
            logger.error(f"Browser worker error: {e}")
            self._browser_error = str(e)
            self._browser_ready.set()
        finally:
            if page:
                try:
                    page.close()
                except Exception:
                    pass
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
            if pw:
                try:
                    pw.stop()
                except Exception:
                    pass

    def _browser_fetch(self, url: str, params: dict = None) -> dict:
        """Send API call to browser worker thread (handles msToken/a_bogus automatically)."""
        if self._browser_error and not self._browser_ready.is_set():
            raise RuntimeError(f"Browser not available: {self._browser_error}")

        req_id = f"req_{int(time.time() * 1000)}_{random.randint(0, 9999)}"
        result_queue = queue.Queue()
        self._browser_queue.put((req_id, url, params or {}, result_queue))
        try:
            _, result, error = result_queue.get(timeout=30)
        except queue.Empty:
            raise RuntimeError("Browser request timed out after 30s")
        if error:
            raise RuntimeError(f"Browser fetch error: {error}")
        return result

    def _generate_cookie(self) -> str:
        base = 1000000000000000000
        web_id = random.randint(base * 6, base * 9)
        return f"novel_web_id={web_id}"

    @staticmethod
    def _generate_ms_token(length: int = 107) -> str:
        """Generate a random msToken (simulated client token for rate-limiting)."""
        base_str = "ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789="
        return "".join(random.choice(base_str) for _ in range(length))

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://fanqienovel.com/",
            "Cookie": self._cookie,
        }

    def _get_mobile_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://novel.snssdk.com/",
        }

    def _request(self, url: str, params: dict = None, headers: dict = None) -> requests.Response:
        if params is None:
            params = {}
        # Auto-add msToken for fanqienovel.com APIs that require anti-crawling signatures
        if "fanqienovel.com" in url and "msToken" not in params:
            params["msToken"] = self._generate_ms_token()
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                time.sleep(BASE_DELAY + random.uniform(0, 0.5))
                resp = self._session.get(url, params=params, headers=headers or self._get_headers(), timeout=15)

                if resp.status_code == 429:
                    wait = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limited, waiting {wait:.1f}s")
                    create_report(
                        ReportType.RATE_LIMIT,
                        f"遭遇速率限制 (HTTP 429)，等待 {wait:.1f}s 后重试 (第{attempt+1}次)",
                        level=ReportLevel.WARNING,
                        context={"url": url, "attempt": attempt + 1, "wait": wait},
                    )
                    time.sleep(wait)
                    self._cookie = self._generate_cookie()
                    continue

                if resp.status_code == 403:
                    create_report(
                        ReportType.AUTH_FAILURE,
                        f"请求被拒绝 (HTTP 403)，可能需要更新认证信息",
                        level=ReportLevel.ERROR,
                        context={"url": url, "attempt": attempt + 1},
                    )
                    self._cookie = self._generate_cookie()
                    time.sleep(2)
                    continue

                if resp.status_code >= 500:
                    create_report(
                        ReportType.NETWORK_ERROR,
                        f"服务器错误 (HTTP {resp.status_code})，将重试",
                        level=ReportLevel.WARNING,
                        context={"url": url, "status_code": resp.status_code},
                    )
                    time.sleep(1 + attempt)
                    continue

                resp.raise_for_status()
                return resp

            except requests.RequestException as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1 + attempt)
                    continue

        create_report(
            ReportType.NETWORK_ERROR,
            f"请求最终失败: {last_error}",
            level=ReportLevel.CRITICAL,
            context={"url": url, "error": str(last_error)},
        )
        raise RuntimeError(f"Max retries exceeded for {url}: {last_error}")

    def search(self, keyword: str, page: int = 0) -> list[dict]:
        logger.info(f"Searching for: {keyword}")
        params = {
            "filter": "127,127,127,127",
            "page_count": "10",
            "page_index": str(page),
            "query_type": "0",
            "query_word": keyword,
        }
        # Use browser fetch to auto-handle msToken/a_bogus signatures
        try:
            data = self._browser_fetch(SEARCH_API, params=params)
        except Exception as e:
            logger.warning(f"Browser fetch failed, falling back to requests: {e}")
            resp = self._request(SEARCH_API, params=params)
            data = resp.json()

        if data.get("_error"):
            raise RuntimeError(f"Search API error: {data}")

        if data.get("code") != 0:
            create_report(
                ReportType.API_CHANGED,
                f"搜索API返回异常: {data.get('message', 'unknown')}",
                level=ReportLevel.ERROR,
                context={"keyword": keyword, "response": str(data)[:200]},
            )
            raise RuntimeError(f"Search API error: {data}")

        book_list = data.get("data", {}).get("search_book_data_list", [])
        results = []
        for b in book_list:
            # Decode encrypted font-mapped text in API response
            raw_name = b.get("book_name", "未知")
            raw_author = b.get("author", "未知")
            raw_abstract = b.get("abstract", "")
            raw_book_abstract = b.get("book_abstract", "")
            abstract_text = raw_book_abstract or raw_abstract
            results.append({
                "book_id": str(b.get("book_id", "")),
                "book_name": self._decode_safe(raw_name),
                "author": self._decode_safe(raw_author),
                "word_count": b.get("word_number", 0),
                "status": {0: "已完结", 1: "连载中"}.get(b.get("creation_status"), "未知"),
                "category": b.get("category", ""),
                "abstract": self._decode_safe(abstract_text),
                "thumb_url": b.get("thumb_url", ""),
            })

        return results

    def _get_chapter_list(self, book_id: str) -> list[dict]:
        logger.info("Fetching chapter list...")
        params = {"bookId": book_id}
        try:
            data = self._browser_fetch(DIRECTORY_API, params=params)
        except Exception as e:
            logger.warning(f"Browser fetch failed for directory, falling back: {e}")
            resp = self._request(DIRECTORY_API, params=params)
            data = resp.json()

        if data.get("code") != 0:
            create_report(
                ReportType.API_CHANGED,
                f"目录API返回异常: {data.get('message', 'unknown')}",
                level=ReportLevel.ERROR,
                context={"book_id": book_id},
            )
            raise RuntimeError(f"Directory API error: {data}")

        all_item_ids = data.get("data", {}).get("allItemIds", [])
        if not all_item_ids:
            create_report(
                ReportType.API_CHANGED,
                "未获取到任何章节 - API可能需要认证或已变更",
                level=ReportLevel.CRITICAL,
                context={"book_id": book_id},
            )
            raise RuntimeError("No chapters found - API may require authentication")

        chapters = []
        for idx, item_id in enumerate(all_item_ids):
            chapters.append({
                "item_id": str(item_id),
                "index": idx,
                "title": f"第{idx + 1}章",
            })
        return chapters

    def _decode_content(self, raw_content: str) -> str:
        buffer = []
        for ch in raw_content:
            code = ord(ch)
            if CODE_MAP[0][0] <= code <= CODE_MAP[0][1]:
                offset = code - CODE_MAP[0][0]
                buffer.append(CHARSET[0][offset] if offset < len(CHARSET[0]) else ch)
            elif CODE_MAP[1][0] <= code <= CODE_MAP[1][1]:
                offset = code - CODE_MAP[1][0]
                buffer.append(CHARSET[1][offset] if offset < len(CHARSET[1]) else ch)
            else:
                buffer.append(ch)
        return "".join(buffer)

    def _decode_safe(self, text: str) -> str:
        """Decode text only if it contains PUA-encoded characters (code points 58344-58716).
        Otherwise return as-is to avoid corrupting already-decoded text."""
        if not text:
            return text
        for ch in text:
            code = ord(ch)
            if (CODE_MAP[0][0] <= code <= CODE_MAP[0][1]) or (CODE_MAP[1][0] <= code <= CODE_MAP[1][1]):
                return self._decode_content(text)
        return text

    def _clean_content(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\\u003c|\\u003e', '', text)
        text = re.sub(r'<header>.*?</header>', '', text, flags=re.DOTALL)
        text = re.sub(r'<footer>.*?</footer>', '', text, flags=re.DOTALL)
        text = re.sub(r'</?article>', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines and not lines[0].startswith('\u3000'):
            lines[0] = '\u3000\u3000' + lines[0]
        return '\n'.join(lines)

    def _fetch_chapter(self, item_id: str) -> Optional[str]:
        # Use browser fetch to auto-handle API signatures
        params = {
            "device_platform": "android",
            "parent_enterfrom": "novel_channel_search.tab.",
            "aid": "2329",
            "platform_id": "1",
            "group_id": item_id,
            "item_id": item_id,
        }
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                time.sleep(BASE_DELAY + random.uniform(0, 0.3))
                # Mobile API on snssdk.com — use direct requests (no msToken needed)
                resp = self._request(CHAPTER_API_MOBILE, params=params,
                                     headers=self._get_mobile_headers())
                data = resp.json()

                if data.get("code") != 0:
                    msg = data.get("message", "unknown")
                    logger.warning(f"Chapter API error for {item_id}: {msg}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1 + attempt)
                        continue
                    return None

                raw_content = data.get("data", {}).get("content", "")
                if not raw_content:
                    return ""

                # 移动端返回 HTML 格式：<article>...<p>段落</p>...</article>
                article_match = re.search(
                    r'<article>([\s\S]*?)</article>', raw_content)
                if article_match:
                    raw_content = article_match.group(1)
                # <p> 标签 → 换行以保留段落结构
                raw_content = re.sub(r'<p\b[^>]*>', '\n', raw_content)

                return self._clean_content(raw_content)

            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1 + attempt)
                    continue

        create_report(
            ReportType.CHAPTER_MISSING,
            f"章节下载失败: {item_id}",
            level=ReportLevel.WARNING,
            context={"item_id": item_id, "error": str(last_error)},
        )
        return None

    def _update_chapter_titles(self, chapters: list[dict]):
        batch_size = 30
        for i in range(0, len(chapters), batch_size):
            batch = chapters[i:i + batch_size]
            ids = [ch["item_id"] for ch in batch]
            params = {"item_ids": ",".join(ids)}
            try:
                time.sleep(BASE_DELAY + random.uniform(0, 0.3))
                try:
                    data = self._browser_fetch(CHAPTER_API, params=params)
                except Exception:
                    resp = self._request(CHAPTER_API, params=params)
                    data = resp.json()
                results = data.get("data", {})
                if isinstance(results, dict):
                    for ch in batch:
                        entry = results.get(ch["item_id"], {})
                        if isinstance(entry, dict) and entry.get("title"):
                            ch["title"] = entry["title"]
            except Exception:
                pass

    def create_download_task(self, book_id: str, book_name: str,
                             author: str = "未知", task_id: str = None) -> CrawlerTask:
        chapters = self._get_chapter_list(book_id)
        if task_id is None:
            task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        task = CrawlerTask(task_id, book_name, len(chapters))
        task.status = "fetching_titles"
        self._tasks[task_id] = task

        self._update_chapter_titles(chapters)

        task.status = "downloading"
        contents = []
        failed_titles = []

        def download_and_report(task: CrawlerTask, chapters, contents, failed_titles):
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                future_map = {
                    executor.submit(self._fetch_chapter, ch["item_id"]): ch
                    for ch in chapters
                }
                ordered = {}
                for future in as_completed(future_map):
                    ch = future_map[future]
                    try:
                        content = future.result()
                        if content:
                            ordered[ch["index"]] = (ch["title"], content)
                        else:
                            failed_titles.append(ch["title"])
                            task.failed += 1
                    except Exception as e:
                        logger.error(f"Error on chapter '{ch['title']}': {e}")
                        failed_titles.append(ch["title"])
                        task.failed += 1
                    task.completed += 1

                for idx in sorted(ordered.keys()):
                    contents.append(ordered[idx])

        download_and_report(task, chapters, contents, failed_titles)

        if failed_titles:
            create_report(
                ReportType.CHAPTER_MISSING,
                f"共 {len(failed_titles)} 章下载失败",
                level=ReportLevel.WARNING,
                context={"book_name": book_name, "failed_count": len(failed_titles),
                         "sample": failed_titles[:5]},
            )
            task.errors = failed_titles[:20]

        if not contents:
            task.status = "failed"
            return task

        task.status = "building_epub"
        safe_title = self._sanitize_filename(book_name)
        output_path = self._save_dir / f"{safe_title}.epub"

        self._epub_builder.build(
            title=book_name,
            author=author,
            description="",
            chapters=contents,
            output_path=output_path,
        )

        task.status = "completed"
        task.output_path = str(output_path)
        task.size_mb = round(output_path.stat().st_size / 1024 / 1024, 2)

        meta_path = output_path.with_suffix(".meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "title": book_name,
                "author": author or "未知",
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }, f, ensure_ascii=False)
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
        }

    def get_history(self) -> list[dict]:
        books = []
        for epub in sorted(self._save_dir.glob("*.epub"), key=lambda x: x.stat().st_mtime, reverse=True):
            meta_path = epub.with_suffix(".meta.json")
            author = "未知"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    author = meta.get("author", "未知")
                except (json.JSONDecodeError, Exception):
                    pass
            books.append({
                "title": epub.stem,
                "author": author,
                "file_path": str(epub),
                "size_mb": round(epub.stat().st_size / 1024 / 1024, 2),
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(epub.stat().st_mtime)),
            })
        return books

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        illegal = '<>:"/\\|?*'
        result = []
        for ch in name:
            if ch in illegal:
                ch = {"<":"＜",">":"＞",":":"：",'"':"＂","/":"／","\\":"＼","|":"｜","?":"？","*":"＊"}.get(ch, "_")
            result.append(ch)
        return "".join(result).strip() or "unnamed"


_crawler_instance: Optional[FanqieCrawler] = None


def get_crawler(save_dir: str = None) -> FanqieCrawler:
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = FanqieCrawler(save_dir=save_dir or DEFAULT_SAVE_DIR)
    return _crawler_instance
