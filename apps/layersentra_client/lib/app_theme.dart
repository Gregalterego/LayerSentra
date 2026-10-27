import 'package:flutter/material.dart';

import 'theme_tokens.dart';

ThemeData layerSentraTheme() {
  const scheme = ColorScheme.dark(
    primary: LayerSentraColors.text,
    onPrimary: LayerSentraColors.background,
    secondary: LayerSentraColors.accent,
    onSecondary: LayerSentraColors.background,
    surface: LayerSentraColors.surface,
    onSurface: LayerSentraColors.text,
    error: Color(0xffff8c93),
    onError: LayerSentraColors.background,
    outline: LayerSentraColors.line,
  );
  final base = ThemeData(useMaterial3: true, colorScheme: scheme);
  const outline = OutlineInputBorder(
    borderRadius: BorderRadius.all(Radius.circular(16)),
    borderSide: BorderSide(color: LayerSentraColors.line),
  );
  return base.copyWith(
    scaffoldBackgroundColor: LayerSentraColors.background,
    appBarTheme: const AppBarTheme(
      backgroundColor: LayerSentraColors.background,
      foregroundColor: LayerSentraColors.text,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: LayerSentraColors.surface,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(22),
        side: const BorderSide(color: LayerSentraColors.line),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: LayerSentraColors.action,
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
        foregroundColor: LayerSentraColors.text,
        textStyle: const TextStyle(fontFamily: 'monospace', fontSize: 12),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(foregroundColor: LayerSentraColors.text),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      filled: true,
      fillColor: LayerSentraColors.surface,
      border: outline,
      enabledBorder: outline,
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.all(Radius.circular(16)),
        borderSide: BorderSide(color: LayerSentraColors.text, width: 2),
      ),
      labelStyle: TextStyle(
        color: LayerSentraColors.muted,
        fontFamily: 'monospace',
        fontSize: 13,
      ),
    ),
    textSelectionTheme: const TextSelectionThemeData(
      cursorColor: LayerSentraColors.accent,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: LayerSentraColors.surface,
      surfaceTintColor: Colors.transparent,
      indicatorColor: LayerSentraColors.text,
      labelTextStyle: const WidgetStatePropertyAll(
        TextStyle(
          color: LayerSentraColors.text,
          fontFamily: 'monospace',
          fontSize: 11,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected)
              ? LayerSentraColors.background
              : LayerSentraColors.muted,
        ),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: LayerSentraColors.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(26)),
    ),
    textTheme: base.textTheme.copyWith(
      headlineMedium: const TextStyle(
        color: LayerSentraColors.text,
        fontSize: 28,
        fontWeight: FontWeight.w500,
        letterSpacing: -.8,
      ),
      labelSmall: const TextStyle(
        color: LayerSentraColors.muted,
        fontFamily: 'monospace',
        fontSize: 11,
        letterSpacing: .8,
      ),
    ),
  );
}
