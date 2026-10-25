# PrintWatch native companion — iOS, Android, macOS, Windows

Flutter application with a native camera/status/filament dashboard and the full
Klipper interface in an embedded WebView. AI continues on the existing PrintWatch
server. This is not a standalone AI engine or a replacement for the server.

## Functions

- Connect to a user-supplied HTTPS server; no personal hosts or printer IPs bundled.
- Native camera view, camera selection, printer progress and filament estimates.
- Start/stop observation on PrintWatch server 0.4.0+, without enabling automatic pause.
- LSC directional controls, disabled until a verified PTZ bridge is configured.
  See [PTZ requirements](../../PTZ.it.md). Direct LSC motion support is not claimed.
- Embedded full Klipper controls; real printer commands are possible there.
- Tailscale HTTPS or a personal HTTPS domain with Basic Authentication.
- Only server addresses are saved in preferences. Credentials are session-only;
  the embedded view requests non-persistent authentication and incognito mode.
- No certificate-validation bypass, plain HTTP or credentials embedded in URLs.
- Polling pauses when the app is backgrounded. No background monitoring or push notifications.

## Development

Use Flutter stable 3.47.7 / Dart 3.13.5 (the generated platform projects target this
SDK) and the platform toolchain. From this directory:

```sh
flutter pub get
flutter analyze
flutter test
flutter run -d macos
```

Build on the matching operating system:

```sh
flutter build macos --release
flutter build ios --release --no-codesign
flutter build apk --debug
flutter build windows --release
```

The Android debug APK is for testing only. Release signing for Android must use a
private upload key and keystore outside Git; provide a private `android/key.properties` with `storeFile`, `storePassword`,
`keyAlias` and `keyPassword`. The release build has no signing key by default.
Do not upload a debug build to a store as a final release.
An unsigned iOS build cannot be installed on a normal iPhone: use Xcode signing
with your own developer team, bundle identifier and an authorized device, or prepare
TestFlight/App Store distribution. No personal development team is committed.
Mac distribution needs your own signing/notarization; Windows needs the Visual Studio
C++ toolchain and WebView2 runtime, and the plugin may require NuGet on PATH.
Use matching plugin requirements from https://inappwebview.dev/docs/intro/ .

Before publication, choose identifiers that you own; `org.printwatch` is a development
placeholder. Review store privacy declarations and plugin privacy manifests. The
repository's CI may build unsigned/test artifacts; it does not publish to stores.

## Server update

The camera and read-only status also work with server 0.2.0. The AI button requires
server 0.4.0. For the previous macOS installation in `~/Applications/PrintWatch`,
extract a fresh source archive to a separate directory on that host and run
`update-macos.command` from the repository root. It backs up code, refuses to
update during an active/paused print and preserves data/models. Then reload the
web dashboard or reconnect the companion. The PTZ bridge is a separate prerequisite.

The phone/desktop running this app must reach the server and, for private Tailscale
URLs, be connected to the right tailnet. Each HTTP service can request its own login.
No server or printer is deployed simply by installing the client.

## Toolchain compatibility

Android is pinned to AGP 8.13.2 / Gradle 8.14.6 / Kotlin 2.2.20 and API 36 because
the stable WebView dependency still references the ProGuard filename removed in
AGP 9. Windows applies Microsoft's transitional coroutine compatibility define
to the pinned WebView plugin only; migrate it when upstream adopts standard
coroutines. These settings are covered by the native build workflow.
