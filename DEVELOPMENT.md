# 开发进度 & 问题记录

> 最后更新: 2026-06-21

## 环境准备 ✅

```bash
git clone https://github.com/haryqs/fanqie-crawler.git
cd fanqie-crawler
pip install -r requirements.txt
python -m playwright install chromium
python app.py
# 打开 http://localhost:5000
```

## 已完成的修改

### 1. 依赖更新 (`requirements.txt`)
- 新增 `playwright>=1.40.0` — 用浏览器自动化绕过番茄小说的反爬签名

### 2. 爬虫核心改造 (`crawler.py`)

#### 问题背景
番茄小说 API 从某个版本开始要求 `msToken` 和 `a_bogus` 两个反爬签名参数，原代码直接调 `requests.get` 会导致：
- 搜索 API 返回空响应 → Flask 500 错误
- 目录/章节 API 同样需要签名

#### 解决方案：懒启动专用浏览器线程 + 请求队列
- 首次需要浏览器签名接口时，懒启动一个专用 daemon 线程运行 Playwright Chromium
- 打开 `fanqienovel.com` 首页，让页面 SDK (bdms.js) 自动加载
- API 调用通过 `queue.Queue` 发送到浏览器线程，由浏览器 `fetch()` 执行
- 浏览器自动注入 `msToken` / `a_bogus` / Cookie 等签名参数
- 浏览器响应中的 `x-tt-zhal` 字体配置会随 JSON 一起返回，用于反混淆解码
- 结果通过队列返回给调用线程
- 浏览器不可用时不影响 `FanqieCrawler` 初始化，调用处会降级到 requests 或章节网页 fallback
- **线程安全**：Flask `threaded=True` 下每个请求在不同线程，但浏览器操作集中在专用线程

#### 新增方法
| 方法 | 作用 |
|------|------|
| `_browser_worker()` | 浏览器专用线程主循环 |
| `_browser_fetch(url, params, include_headers)` | 队列入队 → 等待浏览器执行 → 返回 JSON/响应头 |
| `_font_variant_from_*()` | 从字体文件、页面 HTML 或响应头判断番茄字体混淆变体 |
| `_decode_content(text, variant)` | 按当前字体变体解码 PUA 字符，未知变体不静默乱解 |
| `_fetch_chapter_from_web(item_id)` | 移动端章节 API 空响应时，从 reader SSR 页面提取正文 |
| `_decode_safe(text, variant)` | 安全解码：仅当文本含 PUA 编码字符(58344-58716)时才解码，否则原样返回 |
| `_generate_ms_token()` | 生成随机 msToken（requests 降级时使用） |

#### 修改的方法
| 方法 | 改动 |
|------|------|
| `search()` | 优先用 `_browser_fetch` 调用搜索 API；按 `x-tt-zhal` 选择字体变体并解码搜索结果 |
| `_get_chapter_list()` | 改用 `_browser_fetch`；失败时降级到 requests+msToken |
| `_update_chapter_titles()` | 改用 `_browser_fetch` |
| `_fetch_chapter()` | 移动端 API 为空/非 JSON 时，降级到 reader 页面 SSR 正文 |
| `_request()` | 对 fanqienovel.com 的请求自动附加随机 msToken |
| `EpubBuilder._build_chapter_html()` | 移除 XML declaration，兼容当前 ebooklib nav 生成 |

## 当前状态 ⚠️

### ✅ 正常工作的
- Flask 服务启动 (`python app.py`)
- `FanqieCrawler` 初始化不再强制启动浏览器
- Playwright/Chromium 安装完成后，搜索 API 能返回结果（不再 500）
- 搜索结果书名、作者、简介可解码，已验证 `菜月昴` 返回 10 条且 PUA 字符为 0
- 章节下载可在移动端 API 空响应时走网页 fallback，已验证 `Re0我哥是菜月昴` 前 3 章 EPUB 生成成功
- EPUB 构建已兼容当前 `ebooklib`

### ⚠️ 仍需关注的问题

#### 问题 1：Playwright 环境
**现象**：未执行 `python -m playwright install chromium` 时，搜索会降级到 requests；如果 requests 被番茄返回空响应，搜索仍可能失败。

**处理**：
- 首次部署必须执行 `pip install -r requirements.txt`
- 然后执行 `python -m playwright install chromium`
- 当前机器已完成这两步

#### 问题 2：下载保存路径不明确
**现象**：用户不知道 EPUB 文件保存在哪里。

**当前保存路径**：`C:\Users\<用户名>\Documents\番茄小说\`

**改进方向**：
- 在前端下载完成提示中显示 `output_path`
- 在 `/api/progress` 响应中已包含 `output_path` 字段，前端未展示

## 其他开源参考项目

| 项目 | Stars | 状态 |
|------|-------|------|
| [POf-L/Fanqie-novel-Downloader](https://github.com/POf-L/Fanqie-novel-Downloader) | 1.1k | 活跃（闭源桌面GUI） |
| [Dlmily/Tomato-Novel-Downloader-Lite](https://github.com/Dlmily/Tomato-Novel-Downloader-Lite) | 482 | 使用第三方API |
| [MeoProject/PyFQWeb](https://github.com/MeoProject/PyFQWeb) | 87 | 已归档 |
| [lemnt-ai/fanqie-mcp-server](https://github.com/lemnt-ai/fanqie-mcp-server) | 1 | MCP 服务器 |

## 下次继续开发的步骤

1. **改进 UI** — 显示保存路径、更好的错误提示
2. **性能优化** — 缓存目录数据、控制 reader fallback 并发
3. **字体映射监控** — 如果出现未知字体变体，报告里会给出 font/min_codepoint，按该信息更新映射
4. **端到端测试** — 为搜索、章节 fallback、EPUB 构建增加最小自动化测试
