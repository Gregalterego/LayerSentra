import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

class ServerProfile {
  final Uri dashboard;
  final Uri controls;
  ServerProfile(String dashboardUrl, String controlsUrl)
    : dashboard = validate(dashboardUrl),
      controls = validate(controlsUrl);

  static Uri validate(String value) {
    final uri = Uri.tryParse(value.trim());
    if (uri == null ||
        uri.scheme != 'https' ||
        uri.host.isEmpty ||
        uri.userInfo.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment ||
        (uri.path.isNotEmpty && uri.path != '/')) {
      throw const FormatException(
        'Inserisci un indirizzo HTTPS senza password o sottopercorsi.',
      );
    }
    return uri.replace(path: '/');
  }

  static String suggestedControls(String url) {
    return validate(url).replace(port: 8443).toString();
  }
}

class AuthenticationRequired implements Exception {}

class LayerScanApi {
  final ServerProfile profile;
  final HttpClient _client = HttpClient()
    ..connectionTimeout = const Duration(seconds: 8);
  String? _authorization;
  LayerScanApi(this.profile);

  void authenticate(String user, String password) {
    if (user.contains(':') || user.contains('\n') || password.contains('\n')) {
      throw const FormatException('Credenziali non valide.');
    }
    _authorization = 'Basic ${base64Encode(utf8.encode('$user:$password'))}';
  }

  Future<Uint8List> _request(
    String path, {
    Map<String, dynamic>? body,
    String? token,
  }) async {
    final uri = profile.dashboard.resolve(path);
    if (uri.origin != profile.dashboard.origin) {
      throw StateError('Origine non consentita');
    }
    final request = await _client.openUrl(body == null ? 'GET' : 'POST', uri);
    request.followRedirects = false;
    if (_authorization != null) {
      request.headers.set('Authorization', _authorization!);
    }
    request.headers.set('Cache-Control', 'no-cache');
    if (body != null) {
      request.headers.contentType = ContentType.json;
      request.headers.set('X-LayerScan-Token', token ?? '');
      // Compatibility with servers installed before the product rename.
      request.headers.set('X-LayerSentra-Token', token ?? '');
      request.headers.set('X-PrintWatch-Token', token ?? '');
      request.write(jsonEncode(body));
    }
    final response = await request.close().timeout(const Duration(seconds: 12));
    final bytes = BytesBuilder(copy: false);
    await for (final chunk in response.timeout(const Duration(seconds: 12))) {
      bytes.add(chunk);
      if (bytes.length > 12 * 1024 * 1024) {
        throw const FormatException('Risposta troppo grande');
      }
    }
    if (response.statusCode == 401) throw AuthenticationRequired();
    if (response.statusCode != 200) {
      throw HttpException(
        'HTTP ${response.statusCode}: verifica indirizzo, Tailscale e accesso al server.',
      );
    }
    return bytes.takeBytes();
  }

  Future<Map<String, dynamic>> json(String path) async {
    final value = jsonDecode(utf8.decode(await _request(path)));
    if (value is! Map<String, dynamic>) {
      throw const FormatException('Risposta LayerScan non valida');
    }
    return value;
  }

  Future<Uint8List> frame(String camera) =>
      _request('/api/frame/${Uri.encodeComponent(camera)}');
  Future<void> observe(bool enabled, String token) async {
    await _request(
      '/api/observation',
      body: {'enabled': enabled},
      token: token,
    );
  }

  Future<void> move(String direction, String token) async {
    await _request('/api/ptz', body: {'direction': direction}, token: token);
  }

  void close() {
    _authorization = null;
    _client.close(force: true);
  }
}
