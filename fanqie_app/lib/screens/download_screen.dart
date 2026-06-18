import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/download_provider.dart';

class DownloadScreen extends StatelessWidget {
  const DownloadScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DownloadProvider>();
    final task = provider.currentTask;
    final theme = Theme.of(context);

    return PopScope(
      canPop: task == null || task.isCompleted || task.isFailed,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('下载进行中，无法返回')),
          );
        }
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text(task?.bookName ?? '下载'),
          leading: (task != null && !task.isCompleted && !task.isFailed)
              ? null
              : IconButton(
                  icon: const Icon(Icons.arrow_back),
                  onPressed: () {
                    provider.dismissTask();
                    Navigator.pop(context);
                  },
                ),
        ),
        body: task == null
            ? const Center(child: Text('没有下载任务'))
            : Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (task.isCompleted) ...[
                      const Icon(Icons.check_circle, size: 72, color: Colors.green),
                      const SizedBox(height: 16),
                      Text('下载完成!', style: theme.textTheme.headlineSmall),
                      const SizedBox(height: 8),
                      if (task.sizeMb != null)
                        Text('文件大小: ${task.sizeMb!.toStringAsFixed(1)} MB',
                            style: theme.textTheme.bodyLarge),
                      if (task.failed > 0)
                        Text('${task.failed} 章下载失败',
                            style: TextStyle(color: theme.colorScheme.error)),
                      const SizedBox(height: 24),
                      FilledButton(
                        onPressed: () {
                          provider.dismissTask();
                          Navigator.pop(context);
                        },
                        child: const Text('返回'),
                      ),
                    ] else if (task.isFailed) ...[
                      const Icon(Icons.error, size: 72, color: Colors.red),
                      const SizedBox(height: 16),
                      Text('下载失败', style: theme.textTheme.headlineSmall),
                      const SizedBox(height: 24),
                      FilledButton(
                        onPressed: () {
                          provider.dismissTask();
                          Navigator.pop(context);
                        },
                        child: const Text('返回'),
                      ),
                    ] else ...[
                      SizedBox(
                        width: 72,
                        height: 72,
                        child: CircularProgressIndicator(
                          value: task.progress > 0 ? task.progress / 100 : null,
                          strokeWidth: 6,
                        ),
                      ),
                      const SizedBox(height: 24),
                      Text(task.statusText, style: theme.textTheme.titleLarge),
                      const SizedBox(height: 8),
                      if (task.total > 0)
                        Text(
                          '${task.completed} / ${task.total} 章',
                          style: theme.textTheme.bodyLarge,
                        ),
                      if (task.progress > 0)
                        Text(
                          '${task.progress.toStringAsFixed(1)}%',
                          style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey),
                        ),
                      if (task.failed > 0)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            '${task.failed} 章失败',
                            style: TextStyle(color: theme.colorScheme.error),
                          ),
                        ),
                    ],
                  ],
                ),
              ),
      ),
    );
  }
}
