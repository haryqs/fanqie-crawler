import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/book.dart';
import '../models/download_task.dart';

class ApiException implements Exception {
  final String message;
  const ApiException(this.message);
  @override
  String toString() => message;
}

class ApiService {
  static String get _base => ApiConfig.baseUrl;

  static Future<Map<String, dynamic>> _get(String path) async {
    final url = Uri.parse('$_base$path');
    final resp = await http.get(url).timeout(const Duration(seconds: 10));
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode >= 400) {
      throw ApiException(body['error'] as String? ?? '请求失败');
    }
    return body;
  }

  static Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> data,
  ) async {
    final url = Uri.parse('$_base$path');
    final resp = await http
        .post(url, body: jsonEncode(data), headers: {'Content-Type': 'application/json'})
        .timeout(const Duration(seconds: 10));
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode >= 400) {
      throw ApiException(body['error'] as String? ?? '请求失败');
    }
    return body;
  }

  static Future<bool> healthCheck() async {
    try {
      final body = await _get('/api/health');
      return body['status'] == 'ok';
    } catch (_) {
      return false;
    }
  }

  static Future<List<Book>> search(String keyword) async {
    final body = await _post('/api/search', {'keyword': keyword});
    final results = body['results'] as List<dynamic>? ?? [];
    return results.map((e) => Book.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<String> startDownload(Book book) async {
    final body = await _post('/api/download', {
      'book_id': book.bookId,
      'book_name': book.bookName,
      'author': book.author,
      'thumb_url': book.thumbUrl,
      'abstract': book.abstract,
    });
    return body['task_id'] as String;
  }

  static Future<DownloadTask> getProgress(String taskId) async {
    final body = await _get('/api/progress/$taskId');
    return DownloadTask.fromJson(body);
  }

  static Future<List<Book>> getHistory() async {
    final body = await _get('/api/history');
    final books = body['books'] as List<dynamic>? ?? [];
    return books.map((e) {
      final m = e as Map<String, dynamic>;
      return Book(
        bookId: '',
        bookName: m['title'] as String? ?? '',
        author: m['author'] as String? ?? '',
        wordCount: 0,
        status: '',
        category: '',
        abstract: '',
        thumbUrl: '',
      );
    }).toList();
  }

  static Future<Map<String, dynamic>> getHistoryRaw() async {
    return _get('/api/history');
  }
}
