import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:printwatch_client/main.dart';
import 'package:printwatch_client/server.dart';

void main() {
  test('Server URLs reject plaintext, embedded credentials and paths', () {
    for (final url in [
      'http://watch.example.org',
      'https://user:pass@watch.example.org',
      'https://watch.example.org/private',
      'file:///tmp/test',
    ]) {
      expect(() => ServerProfile.validate(url), throwsFormatException);
    }
    expect(
      ServerProfile.suggestedControls('https://watch.example.org'),
      'https://watch.example.org:8443/',
    );
    expect(ServerProfile.validate('https://watch.example.org:9443').port, 9443);
  });
  testWidgets('Initial screen asks for user server without private defaults', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(const PrintWatchApp());
    await tester.pumpAndSettle();
    expect(find.text('PrintWatch'), findsOneWidget);
    expect(find.text('Collega la stampante'), findsOneWidget);
    final fields = tester.widgetList<TextField>(find.byType(TextField));
    expect(fields.every((field) => field.controller!.text.isEmpty), isTrue);
    await tester.tap(find.text('Collega la stampante'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Inserisci un indirizzo HTTPS'), findsOneWidget);
  });
}
