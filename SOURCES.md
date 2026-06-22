# 多源扩展说明

本项目现在通过 `sources.py` 管理小说来源。每个来源需要提供同一组方法：

- `metadata()`：返回源名称、说明、搜索占位符。
- `search(keyword)`：返回统一格式的书籍列表。
- `create_download_task(book_id, book_name, author, task_id, **kwargs)`：下载并生成 EPUB。
- `get_task_progress(task_id)`：返回下载进度。
- `get_history()`：返回该来源生成的历史文件。

## 当前内置来源

- `fanqie`：番茄小说，保留原有搜索、章节目录、字体解码和 EPUB 生成能力。
- `web`：公开网页 URL，把单页公开文章/章节保存为 EPUB。

## 新增平台

新增平台时，建议在 `sources.py` 里添加一个新的 `Source` 类，然后在 `SourceManager.__init__()` 注册：

```python
self._sources = {
    FanqieSource.source_id: FanqieSource(save_dir=self._save_dir),
    PublicWebSource.source_id: PublicWebSource(save_dir=self._save_dir),
    NewPlatformSource.source_id: NewPlatformSource(save_dir=self._save_dir),
}
```

搜索结果至少应包含：

```python
{
    "book_id": "...",
    "book_name": "...",
    "author": "...",
    "word_count": 0,
    "status": "...",
    "category": "...",
    "abstract": "...",
    "thumb_url": "",
    "source_id": "...",
    "source_name": "..."
}
```

## 边界

工具只面向用户有权访问的公开内容或自有内容。不要实现绕过登录、付费墙、验证码、DRM、访问控制或平台明确禁止抓取规则的逻辑。对需要账号授权的网站，应优先做官方 API、导入本地文件、用户手动导出内容等合规路径。

## 打包

Windows 下运行：

```bat
build_windows.bat
```

产物在 `dist/NovelDownloader`。运行里面的 `NovelDownloader.exe` 后，EPUB 默认保存到 exe 同级目录下的 `downloads` 文件夹。
