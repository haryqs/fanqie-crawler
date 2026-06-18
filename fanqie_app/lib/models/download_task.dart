class DownloadTask {
  final String taskId;
  final String bookName;
  final String status;
  final int completed;
  final int total;
  final int failed;
  final double progress;
  final List<String> errors;
  final String? outputPath;
  final double? sizeMb;

  const DownloadTask({
    required this.taskId,
    required this.bookName,
    required this.status,
    required this.completed,
    required this.total,
    required this.failed,
    required this.progress,
    required this.errors,
    this.outputPath,
    this.sizeMb,
  });

  factory DownloadTask.fromJson(Map<String, dynamic> json) {
    return DownloadTask(
      taskId: json['task_id'] as String? ?? '',
      bookName: json['book_name'] as String? ?? '',
      status: json['status'] as String? ?? 'unknown',
      completed: (json['completed'] as num?)?.toInt() ?? 0,
      total: (json['total'] as num?)?.toInt() ?? 0,
      failed: (json['failed'] as num?)?.toInt() ?? 0,
      progress: (json['progress'] as num?)?.toDouble() ?? 0.0,
      errors: (json['errors'] as List<dynamic>?)?.cast<String>() ?? [],
      outputPath: json['output_path'] as String?,
      sizeMb: (json['size_mb'] as num?)?.toDouble(),
    );
  }

  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';

  String get statusText {
    switch (status) {
      case 'preparing':
        return '准备中...';
      case 'fetching_titles':
        return '获取章节...';
      case 'downloading':
        return '下载中...';
      case 'building_epub':
        return '生成EPUB...';
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      default:
        return status;
    }
  }
}
