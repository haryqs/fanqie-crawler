# 番茄小说 EPUB 一键下载器

搜索书名 → 一键下载全本 → 纯净 EPUB → 微信转存 iOS

---

## 🚀 一键启动

### Windows（双击 `run.bat`）
```
第一步: 双击 run.bat（首次需先执行下面安装步骤）
第二步: 输入书名 → 自动下载
第三步: EPUB 保存在 Documents\番茄小说\
```

### macOS / iOS a-Shell（运行 `run.sh`）
```
$ bash run.sh
```

或直接：
```
$ python3 launcher.py
```

---

## 📦 首次安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活 (Windows)
venv\Scripts\activate

# 激活 (macOS/iOS)
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 📖 使用方法

**交互菜单（推荐）:**
```
python launcher.py
```
菜单选项：
- `[1]` 搜索书名 → 选择 → 下载 EPUB
- `[2]` 输入小说 ID 直接下载
- `[3]` 查看已有下载
- `[4]` 打开保存目录

**命令行模式:**
```bash
python main.py 斗破苍穹
python main.py --book-id 7143038691944959011
```

---

## 📱 iOS 微信转存

| 步骤 | 操作 |
|------|------|
| 1 | 电脑上运行下载（或用 a-Shell 在 iOS 直接跑） |
| 2 | 打开微信 → **文件传输助手** → 发送 EPUB |
| 3 | iPhone 微信中点击文件 → **用其他应用打开** |
| 4 | 选择「**图书**」或「**微信读书**」 |

### iOS 直接运行
安装 [a-Shell](https://apps.apple.com/app/a-shell/id1473805438) → pip install 依赖 → `python3 launcher.py` → 文件在「文件」App 中

---

## 📂 文件位置

```
Windows:  C:\Users\<用户名>\Documents\番茄小说\
macOS:    ~/Documents/番茄小说/
iOS:      文件 App → 我的 iPhone → Documents → 番茄小说
```

---

## 🔧 功能特性

- 模糊书名搜索，自动匹配
- 全本章节并发下载（8 线程）+ 速率限制
- 内容自动解码（反爬字体映射）
- EPUB 标准格式：TOC 目录 + CSS 排版 + 封面嵌入
- 失败自动重试，异常章节跳过不中断

---

## ⚠️ 免责声明

本工具仅供学习交流使用，下载内容请于 24 小时内删除。请尊重版权，勿用于商业用途。
