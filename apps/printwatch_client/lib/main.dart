import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'server.dart';
import 'app_theme.dart';
import 'brand.dart';
import 'theme_tokens.dart';

void main() => runApp(const PrintWatchApp());

class PrintWatchApp extends StatelessWidget {
  const PrintWatchApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'PrintWatch',
    debugShowCheckedModeBanner: false,
    theme: printWatchTheme(),
    home: const ConnectionPage(),
  );
}

class ConnectionPage extends StatefulWidget {
  const ConnectionPage({super.key});
  @override
  State<ConnectionPage> createState() => _ConnectionPageState();
}

class _ConnectionPageState extends State<ConnectionPage> {
  final dashboard = TextEditingController(), controls = TextEditingController();
  String? error;
  bool busy = false;
  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    dashboard.text = prefs.getString('server') ?? '';
    controls.text = prefs.getString('controls') ?? '';
  }

  @override
  void dispose() {
    dashboard.dispose();
    controls.dispose();
    super.dispose();
  }

  Future<void> _connect() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final profile = ServerProfile(
        dashboard.text,
        controls.text.isEmpty
            ? ServerProfile.suggestedControls(dashboard.text)
            : controls.text,
      );
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('server', profile.dashboard.toString());
      await prefs.setString('controls', profile.controls.toString());
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute<void>(builder: (_) => MonitorPage(profile: profile)),
      );
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 540),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(
                  Icons.view_in_ar_rounded,
                  size: 64,
                  color: PrintWatchColors.accent,
                ),
                const SizedBox(height: 22),
                const Center(child: DotWordmark(width: 280)),
                const SizedBox(height: 12),
                const Text(
                  'La tua stampa, sotto controllo.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 20),
                ),
                const SizedBox(height: 28),
                const Text(
                  'Collega il tuo server PrintWatch. L’AI resta sul server; attiva Tailscale se usi un indirizzo privato.',
                ),
                const SizedBox(height: 22),
                TextField(
                  controller: dashboard,
                  keyboardType: TextInputType.url,
                  autocorrect: false,
                  decoration: const InputDecoration(
                    labelText: 'Indirizzo HTTPS di PrintWatch',
                    hintText: 'https://stampa.example.org/',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: controls,
                  keyboardType: TextInputType.url,
                  autocorrect: false,
                  decoration: const InputDecoration(
                    labelText: 'Pannello Klipper (opzionale)',
                    helperText: 'Se vuoto: stesso server, porta 8443',
                    border: OutlineInputBorder(),
                  ),
                ),
                if (error != null)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    child: Text(
                      error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: busy ? null : _connect,
                  icon: const Icon(Icons.link),
                  label: const Text('Collega la stampante'),
                ),
                const SizedBox(height: 18),
                const Text(
                  'Vengono salvati soltanto gli indirizzi. Le password richieste rimangono nella sessione. Serve un server acceso e raggiungibile.',
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class MonitorPage extends StatefulWidget {
  final ServerProfile profile;
  const MonitorPage({super.key, required this.profile});
  @override
  State<MonitorPage> createState() => _MonitorPageState();
}

class _MonitorPageState extends State<MonitorPage> with WidgetsBindingObserver {
  late final PrintWatchApi api;
  Map<String, dynamic>? status, configuration;
  Uint8List? image;
  String? error, imageError;
  String? capturedLabel;
  String camera = 'primary';
  bool working = false, changing = false, paused = false;
  int tab = 0, frameRevision = 0;
  Timer? timer;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    api = PrintWatchApi(widget.profile);
    _refresh();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    timer?.cancel();
    api.close();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    paused = state != AppLifecycleState.resumed;
    timer?.cancel();
    if (!paused) _refresh();
  }

  Future<List<String>?> _credentials() async {
    final user = TextEditingController(), password = TextEditingController();
    final result = await showDialog<List<String>>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Accesso al server'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(widget.profile.dashboard.host),
            TextField(
              controller: user,
              decoration: const InputDecoration(labelText: 'Utente'),
            ),
            TextField(
              controller: password,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Password'),
            ),
            const Text('Le credenziali vengono usate solo in questa sessione.'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annulla'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, [user.text, password.text]),
            child: const Text('Accedi'),
          ),
        ],
      ),
    );
    // Dispose after the dialog transition completes through the next frame.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      user.dispose();
      password.dispose();
    });
    return result;
  }

  Future<void> _refresh() async {
    if (working || paused || !mounted) return;
    timer?.cancel();
    working = true;
    try {
      configuration ??= await api.json('/api/config');
      final next = await api.json('/api/status');
      if (!mounted) return;
      setState(() {
        status = next;
        error = null;
      });
      final cameras = ((configuration!['config'] as Map)['cameras'] as List)
          .where((c) => c['enabled'] == true)
          .toList();
      if (cameras.isNotEmpty && !cameras.any((c) => c['id'] == camera)) {
        camera = cameras.first['id'] as String;
      }
      final cameraState = (next['cameras'] as Map?)?[camera] as Map?;
      if (cameraState?['state'] != 'ok') {
        if (mounted) {
          setState(() {
            image = null;
            imageError = 'Telecamera non disponibile o fotogramma fermo.';
          });
        }
      } else {
        final requestedCamera = camera, revision = frameRevision;
        try {
          final frame = await api.frame(requestedCamera);
          if (mounted &&
              revision == frameRevision &&
              requestedCamera == camera) {
            setState(() {
              image = frame;
              imageError = null;
              capturedLabel = TimeOfDay.now().format(context);
            });
          }
        } catch (e) {
          if (mounted) {
            setState(() {
              image = null;
              imageError = 'Immagine non disponibile: $e';
            });
          }
        }
      }
    } on AuthenticationRequired {
      if (!mounted) return;
      final credentials = await _credentials();
      if (credentials != null) {
        api.authenticate(credentials[0], credentials[1]);
        configuration = null;
      } else {
        paused = true;
        if (mounted) {
          setState(
            () => error = 'Accesso annullato. Tocca Aggiorna per riprovare.',
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          error = 'Collegamento interrotto. $e';
          image = null;
        });
      }
    } finally {
      working = false;
      if (mounted && !paused) {
        timer = Timer(const Duration(seconds: 3), _refresh);
      }
    }
  }

  Future<void> _observe() async {
    setState(() => changing = true);
    try {
      final token = configuration?['observation_token'] as String?;
      if (token == null) {
        throw StateError(
          'Aggiorna il server PrintWatch alla versione 0.4.0 per il controllo AI remoto.',
        );
      }
      await api.observe(status?['monitoring'] != true, token);
      await _refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$e')));
      }
    } finally {
      if (mounted) setState(() => changing = false);
    }
  }

  Future<void> _move(String direction) async {
    setState(() => changing = true);
    try {
      final token = configuration?['ptz_token'] as String?;
      if (token == null) {
        throw StateError('Movimento LSC non configurato sul server.');
      }
      await api.move(direction, token);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$e')));
      }
    } finally {
      if (mounted) setState(() => changing = false);
    }
  }

  Widget _ptz() {
    final capability = (configuration?['capabilities'] as Map?)?['ptz'] as Map?;
    final enabled =
        capability?['enabled'] == true && !changing && error == null;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Text(
              'Movimento telecamera LSC',
              style: TextStyle(fontSize: 19),
            ),
            Text(
              capability?['enabled'] == true
                  ? 'Un tocco, un movimento breve.'
                  : (capability?['reason'] as String? ??
                        'Serve un bridge PTZ configurato sul server.'),
            ),
            Wrap(
              alignment: WrapAlignment.center,
              spacing: 8,
              children: [
                for (final item in [
                  ('up', Icons.arrow_upward),
                  ('left', Icons.arrow_back),
                  ('stop', Icons.stop),
                  ('right', Icons.arrow_forward),
                  ('down', Icons.arrow_downward),
                ])
                  IconButton.filledTonal(
                    tooltip: item.$1,
                    onPressed: enabled ? () => _move(item.$1) : null,
                    icon: Icon(item.$2),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _metric(String label, String value) => SizedBox(
    width: 210,
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall,
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    ),
  );
  String _number(dynamic value, String unit) =>
      value is num ? '${value.toStringAsFixed(1)} $unit' : 'Non disponibile';
  Widget _monitor() {
    final printer = status?['printer'] as Map? ?? {};
    final cameras =
        ((configuration?['config'] as Map?)?['cameras'] as List? ?? [])
            .where((c) => c['enabled'] == true)
            .toList();
    final active = status?['monitoring'] == true;
    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                printer['state'] == 'printing'
                    ? 'Stampa in corso'
                    : 'Stampante: ${printer['state'] ?? 'in collegamento'}',
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            if (cameras.length > 1)
              DropdownButton<String>(
                value: camera,
                items: cameras
                    .map(
                      (c) => DropdownMenuItem(
                        value: c['id'] as String,
                        child: Text(c['name'] as String),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      camera = value;
                      image = null;
                      frameRevision++;
                    });
                    _refresh();
                  }
                },
              ),
          ],
        ),
        const SizedBox(height: 14),
        ClipRRect(
          borderRadius: BorderRadius.circular(22),
          child: AspectRatio(
            aspectRatio: 4 / 3,
            child: ColoredBox(
              color: Colors.black,
              child: image != null
                  ? Image.memory(
                      image!,
                      gaplessPlayback: true,
                      fit: BoxFit.contain,
                    )
                  : Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Text(imageError ?? 'Attendo la telecamera…'),
                      ),
                    ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          error != null
              ? 'Collegamento assente: nessuna immagine corrente.'
              : 'Ultimo fotogramma: ${capturedLabel ?? 'in attesa'}',
        ),
        const SizedBox(height: 18),
        _ptz(),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: status == null || changing || error != null
              ? null
              : _observe,
          icon: Icon(
            active ? Icons.pause_circle_outline : Icons.play_circle_outline,
          ),
          label: Text(active ? 'Ferma analisi AI' : 'Avvia analisi AI'),
        ),
        const SizedBox(height: 12),
        Text(
          active
              ? (printer['state'] == 'printing'
                    ? 'Osservazione richiesta. Verifica lo stato del modello e della camera qui sotto.'
                    : 'AI in attesa di una stampa attiva.')
              : 'Analisi ferma. La telecamera resta disponibile.',
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _metric(
              'Modello AI',
              status?['model'] == 'ready' ? 'Pronto' : 'Non disponibile',
            ),
            _metric(
              'Avanzamento',
              _number((printer['progress'] as num? ?? 0) * 100, '%'),
            ),
            _metric(
              'Modalità',
              status?['action'] == 'pause'
                  ? 'Pausa configurata'
                  : 'Osservazione',
            ),
          ],
        ),
        if (status?['model_error'] != null) Text('${status!['model_error']}'),
        const SizedBox(height: 12),
        const Text(
          'Il pulsante AI abilita soltanto l’osservazione. Il pannello Klipper può inviare comandi reali alla stampante.',
        ),
      ],
    );
  }

  Widget _filament() {
    final filament = status?['filament'] as Map? ?? {};
    final sensors = filament['sensors'] as List? ?? [];
    return ListView(
      padding: const EdgeInsets.all(22),
      children: [
        const Text(
          'Filamento',
          style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 20),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _metric('Consumato', _number(filament['used_m'], 'm')),
            _metric(
              'Sulla bobina',
              _number(filament['spool_remaining_g'], 'g'),
            ),
            _metric('Per finire', _number(filament['remaining_print_g'], 'g')),
            _metric(
              'Autonomia stimata',
              _number(filament['spool_minutes_estimate'], 'min'),
            ),
          ],
        ),
        for (final sensor in sensors)
          ListTile(
            leading: Icon(
              sensor['enabled'] == true ? Icons.sensors : Icons.sensors_off,
            ),
            title: Text('${sensor['name']}'),
            subtitle: Text(
              sensor['enabled'] != true
                  ? 'Disabilitato: non protegge dall’esaurimento'
                  : sensor['detected'] == true
                  ? 'Filamento presente'
                  : 'Filamento assente',
            ),
          ),
        if (filament['warning'] != null)
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text('${filament['warning']}'),
          ),
        const Text(
          'La quantità disponibile è una stima contabile e richiede il peso iniziale sul server. Non sostituisce un sensore o una bilancia.',
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: const FittedBox(
        fit: BoxFit.scaleDown,
        child: DotWordmark(width: 160),
      ),
      actions: [
        TextButton.icon(
          onPressed: status == null || changing || error != null
              ? null
              : _observe,
          icon: Icon(
            status?['monitoring'] == true
                ? Icons.pause_circle_outline
                : Icons.play_circle_outline,
          ),
          label: Text(status?['monitoring'] == true ? 'Ferma AI' : 'Avvia AI'),
        ),
        IconButton(
          tooltip: 'Aggiorna',
          onPressed: () {
            paused = false;
            configuration = null;
            _refresh();
          },
          icon: const Icon(Icons.refresh),
        ),
      ],
    ),
    body: Column(
      children: [
        if (error != null)
          MaterialBanner(
            content: Text(error!),
            actions: [
              TextButton(
                onPressed: () {
                  paused = false;
                  _refresh();
                },
                child: const Text('Riprova'),
              ),
            ],
          ),
        Expanded(child: tab == 0 ? _monitor() : _filament()),
      ],
    ),
    bottomNavigationBar: NavigationBar(
      selectedIndex: tab,
      onDestinationSelected: (value) {
        if (value == 2) {
          Navigator.push(
            context,
            MaterialPageRoute<void>(
              builder: (_) => KlipperPage(
                url: widget.profile.controls,
                dashboard: widget.profile.dashboard,
              ),
            ),
          );
        } else {
          setState(() => tab = value);
        }
      },
      destinations: const [
        NavigationDestination(
          icon: Icon(Icons.videocam_outlined),
          label: 'Stampa',
        ),
        NavigationDestination(
          icon: Icon(Icons.donut_large),
          label: 'Filamento',
        ),
        NavigationDestination(icon: Icon(Icons.tune), label: 'Klipper'),
      ],
    ),
  );
}

class KlipperPage extends StatefulWidget {
  final Uri url;
  final Uri dashboard;
  const KlipperPage({super.key, required this.url, required this.dashboard});
  @override
  State<KlipperPage> createState() => _KlipperPageState();
}

class _KlipperPageState extends State<KlipperPage> {
  String? error;
  int authAttempts = 0;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Pannello Klipper')),
    body: Column(
      children: [
        const Padding(
          padding: EdgeInsets.all(8),
          child: Text(
            'Comandi reali alla stampante · verifica sempre lo stato prima di agire.',
          ),
        ),
        if (error != null)
          Padding(padding: const EdgeInsets.all(12), child: Text(error!)),
        Expanded(
          child: InAppWebView(
            initialUrlRequest: URLRequest(url: WebUri(widget.url.toString())),
            initialSettings: InAppWebViewSettings(
              useShouldOverrideUrlLoading: true,
              incognito: true,
              javaScriptEnabled: true,
              supportMultipleWindows: false,
            ),
            shouldOverrideUrlLoading: (controller, action) async =>
                (action.request.url?.origin == widget.url.origin ||
                    (action.isForMainFrame != true &&
                        action.request.url?.origin == widget.dashboard.origin))
                ? NavigationActionPolicy.ALLOW
                : NavigationActionPolicy.CANCEL,
            onReceivedError: (controller, request, failure) {
              if (request.isForMainFrame == true) {
                setState(
                  () => error = 'Pannello non raggiungibile: controlla Tailscale e indirizzo.',
                );
              }
            },
            onReceivedHttpAuthRequest: (controller, challenge) async {
              if (challenge.protectionSpace.host != widget.url.host ||
                  challenge.protectionSpace.port != widget.url.port ||
                  authAttempts++ > 2) {
                return HttpAuthResponse(action: HttpAuthResponseAction.CANCEL);
              }
              final user = TextEditingController(),
                  password = TextEditingController();
              final credentials = await showDialog<List<String>>(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Accesso Klipper'),
                  content: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(widget.url.host),
                      TextField(
                        controller: user,
                        decoration: const InputDecoration(labelText: 'Utente'),
                      ),
                      TextField(
                        controller: password,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Password',
                        ),
                      ),
                    ],
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Annulla'),
                    ),
                    FilledButton(
                      onPressed: () =>
                          Navigator.pop(context, [user.text, password.text]),
                      child: const Text('Accedi'),
                    ),
                  ],
                ),
              );
              WidgetsBinding.instance.addPostFrameCallback((_) {
                user.dispose();
                password.dispose();
              });
              if (credentials == null) {
                return HttpAuthResponse(action: HttpAuthResponseAction.CANCEL);
              }
              return HttpAuthResponse(
                username: credentials[0],
                password: credentials[1],
                permanentPersistence: false,
                action: HttpAuthResponseAction.PROCEED,
              );
            },
          ),
        ),
      ],
    ),
  );
}
