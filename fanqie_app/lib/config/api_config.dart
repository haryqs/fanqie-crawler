import 'package:shared_preferences/shared_preferences.dart';

class ApiConfig {
  static const String _key = 'server_url';
  static const String _defaultHost = '127.0.0.1';
  static const int _defaultPort = 5000;

  static String _cachedUrl = 'http://$_defaultHost:$_defaultPort';

  static String get baseUrl => _cachedUrl;

  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _cachedUrl = prefs.getString(_key) ?? 'http://$_defaultHost:$_defaultPort';
  }

  static Future<void> setServer(String host, int port) async {
    final url = 'http://$host:$port';
    _cachedUrl = url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, url);
  }

  static String get defaultHost => _defaultHost;
  static int get defaultPort => _defaultPort;
}
