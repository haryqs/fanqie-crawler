# 番茄小说下载器 - 跨平台客户端

基于 Flutter 的跨平台客户端，支持 iOS、Android、Windows。

## 架构

```
Flutter App (iOS/Android/Windows)
    │  HTTP REST API
    ▼
Python Flask 后端 (app.py + crawler.py)
    │  爬虫引擎
    ▼
番茄小说 API → EPUB 文件
```

## 环境要求

- Flutter SDK >= 3.2.0
- Dart >= 3.2.0

## 快速开始

```bash
# 1. 安装依赖
cd fanqie_app
flutter pub get

# 2. 确保 Python 后端已启动 (见项目根目录 README)

# 3. 运行
flutter run

# 4. 构建
flutter build apk       # Android
flutter build ios       # iOS (需要 macOS)
flutter build windows   # Windows
```

## 项目结构

```
lib/
├── main.dart            # 入口
├── app.dart             # MaterialApp + 底部导航
├── config/
│   └── api_config.dart  # 服务器地址配置 (支持自定义 IP:Port)
├── models/
│   ├── book.dart        # 书籍模型
│   └── download_task.dart # 下载任务模型
├── services/
│   └── api_service.dart # API 客户端 (搜索/下载/进度/历史)
├── providers/
│   ├── search_provider.dart   # 搜索状态管理
│   └── download_provider.dart # 下载状态管理 (含轮询)
├── screens/
│   ├── search_screen.dart     # 搜索页
│   ├── download_screen.dart   # 下载进度页
│   ├── history_screen.dart    # 书架/历史页
│   └── settings_screen.dart   # 设置页 (服务器连接配置)
└── widgets/
    └── book_card.dart         # 书籍卡片组件
```
