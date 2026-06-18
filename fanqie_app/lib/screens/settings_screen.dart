import 'package:flutter/material.dart';
import '../config/api_config.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _hostController = TextEditingController();
  final _portController = TextEditingController();
  bool _checking = false;
  bool? _connected;

  @override
  void initState() {
    super.initState();
    _hostController.text = ApiConfig.defaultHost;
    _portController.text = ApiConfig.defaultPort.toString();
    _loadServer();
  }

  Future<void> _loadServer() async {
    await ApiConfig.init();
    final url = ApiConfig.baseUrl;
    final uri = Uri.parse(url);
    _hostController.text = uri.host;
    _portController.text = uri.port.toString();
  }

  Future<void> _checkConnection() async {
    setState(() {
      _checking = true;
      _connected = null;
    });
    await ApiConfig.setServer(
      _hostController.text.trim(),
      int.tryParse(_portController.text.trim()) ?? 5000,
    );
    final ok = await ApiService.healthCheck();
    setState(() {
      _checking = false;
      _connected = ok;
    });
  }

  @override
  void dispose() {
    _hostController.dispose();
    _portController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('服务器连接', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        flex: 3,
                        child: TextField(
                          controller: _hostController,
                          decoration: const InputDecoration(
                            labelText: '主机地址',
                            border: OutlineInputBorder(),
                            isDense: true,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        flex: 1,
                        child: TextField(
                          controller: _portController,
                          decoration: const InputDecoration(
                            labelText: '端口',
                            border: OutlineInputBorder(),
                            isDense: true,
                          ),
                          keyboardType: TextInputType.number,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      FilledButton.icon(
                        onPressed: _checking ? null : _checkConnection,
                        icon: _checking
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.wifi_find, size: 18),
                        label: const Text('测试连接'),
                      ),
                      const SizedBox(width: 12),
                      if (_connected == true)
                        const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.check_circle, color: Colors.green, size: 20),
                            SizedBox(width: 4),
                            Text('已连接', style: TextStyle(color: Colors.green)),
                          ],
                        ),
                      if (_connected == false)
                        const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.error, color: Colors.red, size: 20),
                            SizedBox(width: 4),
                            Text('无法连接', style: TextStyle(color: Colors.red)),
                          ],
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('使用说明', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 12),
                  _buildStep('1. 在电脑上运行 python app.py 启动服务'),
                  _buildStep('2. 确保手机和电脑在同一局域网'),
                  _buildStep('3. 在设置中输入电脑的局域网 IP 地址'),
                  _buildStep('4. 搜索书名并下载 EPUB'),
                  _buildStep('5. EPUB 保存在电脑上，可通过微信发送到手机'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('关于', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 8),
                  const Text('番茄小说下载器 v1.0.0'),
                  const SizedBox(height: 4),
                  const Text('跨平台客户端 · Flutter'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(text, style: const TextStyle(fontSize: 14)),
    );
  }
}
