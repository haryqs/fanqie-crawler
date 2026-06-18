import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/search_provider.dart';
import '../providers/download_provider.dart';
import '../widgets/book_card.dart';
import 'download_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _doSearch() {
    final keyword = _controller.text;
    _focusNode.unfocus();
    context.read<SearchProvider>().search(keyword);
  }

  void _onBookTap(book) async {
    final downloadProvider = context.read<DownloadProvider>();
    if (downloadProvider.isDownloading) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('有下载任务正在进行中')),
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(book.bookName),
        content: Text('作者: ${book.author}\n${book.wordCountText} · ${book.status}'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('下载')),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      try {
        await downloadProvider.startDownload(book);
        if (mounted) {
          Navigator.push(context, MaterialPageRoute(builder: (_) => const DownloadScreen()));
        }
      } on ApiException catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('下载失败: $e')));
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<SearchProvider>();
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('番茄小说下载器'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: SearchBar(
              controller: _controller,
              focusNode: _focusNode,
              hintText: '输入书名搜索...',
              leading: const Icon(Icons.search),
              trailing: [
                IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _controller.clear();
                    provider.clear();
                  },
                ),
              ],
              onSubmitted: (_) => _doSearch(),
              onTapOutside: (_) => _focusNode.unfocus(),
            ),
          ),
          if (provider.loading)
            const Expanded(child: Center(child: CircularProgressIndicator())),
          if (provider.error != null && !provider.loading)
            Expanded(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
                    const SizedBox(height: 12),
                    Text(provider.error!, style: TextStyle(color: theme.colorScheme.error)),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: () => provider.search(provider.keyword),
                      child: const Text('重试'),
                    ),
                  ],
                ),
              ),
            ),
          if (!provider.loading && provider.error == null && provider.results.isNotEmpty)
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: provider.results.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (context, i) => BookCard(
                  book: provider.results[i],
                  onTap: () => _onBookTap(provider.results[i]),
                ),
              ),
            ),
          if (!provider.loading && provider.error == null && provider.results.isEmpty && provider.keyword.isNotEmpty)
            const Expanded(child: Center(child: Text('未找到相关小说'))),
          if (provider.keyword.isEmpty)
            const Expanded(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.menu_book_outlined, size: 64, color: Colors.grey),
                    SizedBox(height: 16),
                    Text('输入书名开始搜索', style: TextStyle(color: Colors.grey, fontSize: 16)),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
