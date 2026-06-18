import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/book.dart';
import '../models/download_task.dart';
import '../services/api_service.dart';

class DownloadProvider extends ChangeNotifier {
  DownloadTask? _currentTask;
  Timer? _pollTimer;

  DownloadTask? get currentTask => _currentTask;
  bool get isDownloading => _currentTask != null && !_currentTask!.isCompleted && !_currentTask!.isFailed;

  Future<void> startDownload(Book book) async {
    final taskId = await ApiService.startDownload(book);
    _currentTask = DownloadTask(
      taskId: taskId,
      bookName: book.bookName,
      status: 'preparing',
      completed: 0,
      total: 0,
      failed: 0,
      progress: 0,
      errors: [],
    );
    notifyListeners();
    _startPolling(taskId);
  }

  void _startPolling(String taskId) {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (_) async {
      try {
        final task = await ApiService.getProgress(taskId);
        _currentTask = task;
        notifyListeners();
        if (task.isCompleted || task.isFailed) {
          _pollTimer?.cancel();
        }
      } catch (_) {}
    });
  }

  void dismissTask() {
    _pollTimer?.cancel();
    _currentTask = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }
}
