# 开发进度 & 问题记录

> 最后更新: 2026-06-18

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

#### 解决方案：专用浏览器线程 + 请求队列
- 启动一个专用 daemon 线程运行 Playwright Chromium
- 打开 `fanqienovel.com` 首页，让页面 SDK (bdms.js) 自动加载
- API 调用通过 `queue.Queue` 发送到浏览器线程，由浏览器 `fetch()` 执行
- 浏览器自动注入 `msToken` / `a_bogus` / Cookie 等签名参数
- 结果通过队列返回给调用线程
- **线程安全**：Flask `threaded=True` 下每个请求在不同线程，但浏览器操作集中在专用线程

#### 新增方法
| 方法 | 作用 |
|------|------|
| `_browser_worker()` | 浏览器专用线程主循环 |
| `_browser_fetch(url, params)` | 队列入队 → 等待浏览器执行 → 返回 JSON |
| `_decode_safe(text)` | 安全解码：仅当文本含 PUA 编码字符(58344-58716)时才解码，否则原样返回 |
| `_generate_ms_token()` | 生成随机 msToken（requests 降级时使用） |

#### 修改的方法
| 方法 | 改动 |
|------|------|
| `search()` | 改用 `_browser_fetch` 调用搜索 API；搜索结果字段用 `_decode_safe` 解码 |
| `_get_chapter_list()` | 改用 `_browser_fetch`；失败时降级到 requests+msToken |
| `_update_chapter_titles()` | 改用 `_browser_fetch` |
| `_fetch_chapter()` | 保持用 requests（移动端 API 在 snssdk.com，不需要签名） |
| `_request()` | 对 fanqienovel.com 的请求自动附加随机 msToken |

## 当前状态 ⚠️

### ✅ 正常工作的
- Flask 服务启动 (`python app.py`)
- 浏览器线程初始化和页面加载
- 搜索 API 能返回结果（不再 500）

### ❌ 尚未解决的问题

#### 问题 1：搜索结果文字乱码/方框
**现象**：搜索结果中的书名、作者、简介部分文字显示为"方框"或错误字符。

**原因分析**：
- 番茄小说 API 使用自定义字体加密（PUA 码点映射到真实汉字）
- `CODE_MAP` + `CHARSET` 映射表 (`crawler.py:38-42`) 可能已过期
- 当前 `_decode_safe()` 仅在检测到 PUA 码点时才解码，但映射表本身可能不匹配
- 浏览器 `fetch()` 返回的是原始 JSON，不会自动解码字体

**排查方向**：
1. 用浏览器 DevTools 抓取真实搜索请求的 response body
2. 对比加密字符与实际显示的汉字，更新 `CODE_MAP` / `CHARSET` 表
3. 或者从番茄小说页面提取最新字体文件和映射表

#### 问题 2：下载触发反爬虫预警，内容下载失败
**现象**：点击下载后弹出"反爬虫预警"，章节下载失败。

**可能原因**：
- 移动端章节 API (`novel.snssdk.com/api/novel/book/reader/full/v1`) 可能有频率限制或需要额外参数
- 目录 API 通过浏览器队列调用，大量并发请求可能触发风控
- 章节标题 API (`fanqienovel.com/api/reader/full`) 的批量调用可能触发限制

**排查方向**：
1. 在浏览器线程中增加请求间隔 (`time.sleep`)
2. 检查移动端 API 是否需要特定的 `device_platform` / `aid` 参数
3. 尝试通过浏览器 `fetch()` 调用移动端 API（但跨域可能被 CORS 阻止）
4. 参考其他项目如 `POf-L/Fanqie-novel-Downloader` 的实现

#### 问题 3：下载保存路径不明确
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

1. **修复文字编码** — 从浏览器抓取最新 API 响应，更新 `CODE_MAP` / `CHARSET`
2. **修复下载流程** — 测试目录 API 和章节 API 的具体失败原因
3. **改进 UI** — 显示保存路径、更好的错误提示
4. **性能优化** — 减少浏览器调用次数（缓存目录数据等）
