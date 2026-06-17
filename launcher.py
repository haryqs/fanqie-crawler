"""
番茄小说一键下载器 - 交互式启动菜单
Windows/macOS/iOS 通用，输入书名即可下载 EPUB
"""

import os
import sys
import platform
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from main import FanqieCrawler

IS_IOS = platform.system() == "iOS" or os.environ.get("ISH") == "1"
IS_WIN = platform.system() == "Windows"
SAVE_DIR = os.path.expanduser("~/Documents/番茄小说") if IS_IOS else os.path.expanduser("~/Documents/番茄小说")
if IS_WIN:
    SAVE_DIR = os.path.expanduser("~/Documents/番茄小说")


def clear_screen():
    os.system("cls" if IS_WIN else "clear")


def print_header():
    clear_screen()
    print("=" * 50)
    print("    📚 番茄小说 EPUB 一键下载器")
    print("    Fanqie Novel One-Click Downloader")
    print("=" * 50)
    if IS_IOS:
        print("    📱 iOS 模式 — 文件保存在「文件」App 可找到")
    print()


def print_menu():
    print("  [1] 搜索书名并下载")
    print("  [2] 输入小说 ID 直接下载")
    print("  [3] 查看保存目录")
    print("  [4] 打开保存目录")
    print("  [0] 退出")
    print()


def search_and_download(crawler: FanqieCrawler):
    keyword = input("\n📖 请输入小说名称（支持模糊搜索）: ").strip()
    if not keyword:
        print("❌ 书名不能为空")
        input("\n按 Enter 返回...")
        return

    try:
        results = crawler.search(keyword)
    except Exception as e:
        print(f"\n❌ 搜索失败: {e}")
        input("\n按 Enter 返回...")
        return

    if not results:
        print(f"\n❌ 未找到与「{keyword}」相关的小说")
        input("\n按 Enter 返回...")
        return

    print(f"\n✅ 找到 {len(results)} 本书:\n")

    for i, book in enumerate(results):
        status_tag = "✓" if book["status"] == "已完结" else "◎"
        print(f"  [{i + 1}] {book['book_name']}")
        print(f"      作者: {book['author']} | {status_tag} {book['status']}")
        print(f"      字数: {book['word_count']}字 | {book['category']}")
        if book.get("abstract"):
            abstract = book["abstract"][:80].replace("\n", " ")
            print(f"      简介: {abstract}...")
        print()

    choice = input(f"请选择 (1-{len(results)}，输入 0 返回): ").strip()
    try:
        idx = int(choice) - 1
        if idx < 0:
            return
        selected = results[idx]
    except (ValueError, IndexError):
        print("❌ 无效选择")
        input("\n按 Enter 返回...")
        return

    print(f"\n开始下载《{selected['book_name']}》...")
    try:
        result = crawler.download_book(
            book_id=selected["book_id"],
            title=selected["book_name"],
            author=selected["author"],
            description=selected.get("abstract", ""),
            cover_url=selected.get("thumb_url", ""),
        )

        size_mb = result.stat().st_size / 1024 / 1024
        print(f"\n{'=' * 50}")
        print(f"✅ 下载完成！")
        print(f"   书名: {selected['book_name']}")
        print(f"   作者: {selected['author']}")
        print(f"   大小: {size_mb:.1f} MB")
        print(f"   路径: {result}")
        print(f"{'=' * 50}")

        if IS_IOS:
            print("\n📱 iOS 提示:")
            print("   1. 打开「文件」App")
            print("   2. 进入「我的 iPhone」→「Documents」→「番茄小说」")
            print("   3. 点击 EPUB → 用「图书」App 打开")
            print("   4. 或通过「分享」→ 发送到微信")
        else:
            print("\n💡 提示:")
            print("   - 双击 EPUB 文件即可用默认阅读器打开")
            print("   - 可通过微信「文件传输助手」发送到手机")
            open_folder = input("\n📂 要打开保存目录吗？[y/N]: ").strip().lower()
            if open_folder in ("y", "yes"):
                folder = str(Path(result).parent)
                if IS_WIN:
                    os.startfile(folder)
                else:
                    import subprocess
                    subprocess.run(["open", folder])

    except Exception as e:
        print(f"\n❌ 下载失败: {e}")

    input("\n按 Enter 返回菜单...")


def download_by_id(crawler: FanqieCrawler):
    book_id = input("\n📖 请输入小说 ID: ").strip()
    if not book_id:
        print("❌ ID 不能为空")
        input("\n按 Enter 返回...")
        return

    print(f"\n正在获取小说信息并下载...")
    try:
        result = crawler.download_book(book_id)
        size_mb = result.stat().st_size / 1024 / 1024
        print(f"\n{'=' * 50}")
        print(f"✅ 下载完成！")
        print(f"   大小: {size_mb:.1f} MB")
        print(f"   路径: {result}")
        print(f"{'=' * 50}")
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")

    input("\n按 Enter 返回菜单...")


def show_save_dir():
    save_path = Path(SAVE_DIR)
    print(f"\n📂 保存目录: {save_path}")

    if save_path.exists():
        epubs = list(save_path.glob("*.epub"))
        if epubs:
            print(f"\n📚 已有 {len(epubs)} 本小说:\n")
            for f in sorted(epubs, key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                size_mb = f.stat().st_size / 1024 / 1024
                print(f"  📖 {f.stem}  ({size_mb:.1f} MB)")
        else:
            print("\n📭 还没有下载过小说")
    else:
        print("\n📭 保存目录尚不存在")

    input("\n按 Enter 返回菜单...")


def open_save_dir():
    save_path = Path(SAVE_DIR)
    save_path.mkdir(parents=True, exist_ok=True)
    folder = str(save_path)
    print(f"\n📂 打开 {folder} ...")
    try:
        if IS_WIN:
            os.startfile(folder)
        elif IS_IOS:
            print("📱 在 iOS 上请手动打开「文件」App → 番茄小说")
        else:
            import subprocess
            subprocess.run(["open", folder])
    except Exception as e:
        print(f"❌ 无法打开目录: {e}")

    input("\n按 Enter 返回菜单...")


def main():
    crawler = FanqieCrawler(save_dir=SAVE_DIR)

    while True:
        print_header()
        print_menu()
        choice = input("👉 请输入选项: ").strip()

        if choice == "1":
            search_and_download(crawler)
        elif choice == "2":
            download_by_id(crawler)
        elif choice == "3":
            show_save_dir()
        elif choice == "4":
            open_save_dir()
        elif choice == "0":
            print("\n👋 再见！")
            break
        else:
            print("\n❌ 无效选项，请重新选择")
            input("按 Enter 继续...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        input("按 Enter 退出...")
        sys.exit(1)
