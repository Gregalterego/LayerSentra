import 'package:flutter/material.dart';

import 'theme_tokens.dart';

ThemeData layerSentraTheme() {
  const scheme = ColorScheme.dark(
    primary: LayerScanColors.text,
    onPrimary: LayerScanColors.background,
    secondary: LayerScanColors.accent,
    onSecondary: LayerScanColors.background,
    surface: LayerScanColors.surface,
    onSurface: LayerScanColors.text,
    error: Color(0xffff8c93),
    onError: LayerScanColors.background,
    outline: LayerScanColors.line,
  );
  final base = ThemeData(useMaterial3: true, colorScheme: scheme);
  const outline = OutlineInputBorder(
    borderRadius: BorderRadius.all(Radius.circular(16)),
    borderSide: BorderSide(color: LayerScanColors.line),
  );
  return base.copyWith(
    scaffoldBackgroundColor: LayerScanColors.background,
    appBarTheme: const AppBarTheme(
      backgroundColor: LayerScanColors.background,
      foregroundColor: LayerScanColors.text,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: LayerScanColors.surface,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(22),
        side: const BorderSide(color: LayerScanColors.line),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: LayerScanColors.action,
        foregroundColor: Colors.white,
        minimumSize: const Size(44, 46),
        shape: const StadiumBorder(),
        textStyle: const TextStyle(
          fontFamily: 'monospace',
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: LayerScanColors.text,
        textStyle: const TextStyle(fontFamily: 'monospace', fontSize: 12),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(foregroundColor: LayerScanColors.text),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      filled: true,
      fillColor: LayerScanColors.surface,
      border: outline,
      enabledBorder: outline,
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.all(Radius.circular(16)),
        borderSide: BorderSide(color: LayerScanColors.text, width: 2),
      ),
      labelStyle: TextStyle(
        color: LayerScanColors.muted,
        fontFamily: 'monospace',
        fontSize: 13,
      ),
    ),
    textSelectionTheme: const TextSelectionThemeData(
      cursorColor: LayerScanColors.accent,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: LayerScanColors.surface,
      surfaceTintColor: Colors.transparent,
      indicatorColor: LayerScanColors.text,
      labelTextStyle: const WidgetStatePropertyAll(
        TextStyle(
          color: LayerScanColors.text,
          fontFamily: 'monospace',
          fontSize: 11,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected)
              ? LayerScanColors.background
              : LayerScanColors.muted,
        ),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: LayerScanColors.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(26)),
    ),
    textTheme: base.textTheme.copyWith(
      headlineMedium: const TextStyle(
        color: LayerScanColors.text,
        fontSize: 28,
        fontWeight: FontWeight.w500,
        letterSpacing: -.8,
      ),
      labelSmall: const TextStyle(
        color: LayerScanColors.muted,
        fontFamily: 'monospace',
        fontSize: 11,
        letterSpacing: .8,
      ),
    ),
  );
}
