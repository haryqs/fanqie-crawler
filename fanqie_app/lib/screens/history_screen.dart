import 'package:flutter/material.dart';
import '../services/api_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<Map<String, dynamic>> _books = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await ApiService.getHistoryRaw();
      setState(() {
        _books = (data['books'] as List<dynamic>?)?.cast<Map<String, dynamic>>() ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = '加载失败';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('书架'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadHistory,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                      const SizedBox(height: 12),
                      OutlinedButton(onPressed: _loadHistory, child: const Text('重试')),
                    ],
                  ),
                )
              : _books.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.library_books_outlined, size: 64, color: Colors.grey),
                          SizedBox(height: 16),
                          Text('还没有下载过小说', style: TextStyle(color: Colors.grey, fontSize: 16)),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadHistory,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: _books.length,
                        separatorBuilder: (_, __) => const Divider(),
                        itemBuilder: (context, i) {
                          final book = _books[i];
                          final title = book['title'] as String? ?? '';
                          final author = book['author'] as String? ?? '';
                          final size = (book['size_mb'] as num?)?.toDouble();
                          final date = book['downloaded_at'] as String? ?? '';

                          return ListTile(
                            leading: const Icon(Icons.menu_book, size: 40),
                            title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
                            subtitle: Text('$author  ${size?.toStringAsFixed(1) ?? "?"} MB'),
                            trailing: Text(date, style: theme.textTheme.bodySmall),
                          );
                        },
                      ),
                    ),
    );
  }
}
