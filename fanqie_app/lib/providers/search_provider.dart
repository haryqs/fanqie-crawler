import 'package:flutter/foundation.dart';
import '../models/book.dart';
import '../services/api_service.dart';

class SearchProvider extends ChangeNotifier {
  List<Book> _results = [];
  bool _loading = false;
  String? _error;
  String _keyword = '';

  List<Book> get results => _results;
  bool get loading => _loading;
  String? get error => _error;
  String get keyword => _keyword;

  Future<void> search(String keyword) async {
    _keyword = keyword.trim();
    if (_keyword.isEmpty) {
      _error = '请输入书名';
      notifyListeners();
      return;
    }

    _loading = true;
    _error = null;
    _results = [];
    notifyListeners();

    try {
      _results = await ApiService.search(_keyword);
      if (_results.isEmpty) {
        _error = '未找到相关小说';
      }
    } on ApiException catch (e) {
      _error = e.message;
    } catch (e) {
      _error = '搜索失败: 无法连接到服务器';
    }

    _loading = false;
    notifyListeners();
  }

  void clear() {
    _results = [];
    _error = null;
    _keyword = '';
    notifyListeners();
  }
}
