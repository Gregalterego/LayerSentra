import 'package:flutter/material.dart';

import 'theme_tokens.dart';

ThemeData printWatchTheme() {
  const scheme = ColorScheme.dark(
    primary: PrintWatchColors.text,
    onPrimary: PrintWatchColors.background,
    secondary: PrintWatchColors.accent,
    onSecondary: PrintWatchColors.background,
    surface: PrintWatchColors.surface,
    onSurface: PrintWatchColors.text,
    error: Color(0xffff8c93),
    onError: PrintWatchColors.background,
    outline: PrintWatchColors.line,
  );
  final base = ThemeData(useMaterial3: true, colorScheme: scheme);
  const outline = OutlineInputBorder(
    borderRadius: BorderRadius.all(Radius.circular(16)),
    borderSide: BorderSide(color: PrintWatchColors.line),
  );
  return base.copyWith(
    scaffoldBackgroundColor: PrintWatchColors.background,
    appBarTheme: const AppBarTheme(
      backgroundColor: PrintWatchColors.background,
      foregroundColor: PrintWatchColors.text,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: PrintWatchColors.surface,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(22),
        side: const BorderSide(color: PrintWatchColors.line),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: PrintWatchColors.action,
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
        foregroundColor: PrintWatchColors.text,
        textStyle: const TextStyle(fontFamily: 'monospace', fontSize: 12),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(foregroundColor: PrintWatchColors.text),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      filled: true,
      fillColor: PrintWatchColors.surface,
      border: outline,
      enabledBorder: outline,
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.all(Radius.circular(16)),
        borderSide: BorderSide(color: PrintWatchColors.text, width: 2),
      ),
      labelStyle: TextStyle(
        color: PrintWatchColors.muted,
        fontFamily: 'monospace',
        fontSize: 13,
      ),
    ),
    textSelectionTheme: const TextSelectionThemeData(
      cursorColor: PrintWatchColors.accent,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: PrintWatchColors.surface,
      surfaceTintColor: Colors.transparent,
      indicatorColor: PrintWatchColors.text,
      labelTextStyle: const WidgetStatePropertyAll(
        TextStyle(
          color: PrintWatchColors.text,
          fontFamily: 'monospace',
          fontSize: 11,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected)
              ? PrintWatchColors.background
              : PrintWatchColors.muted,
        ),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: PrintWatchColors.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(26)),
    ),
    textTheme: base.textTheme.copyWith(
      headlineMedium: const TextStyle(
        color: PrintWatchColors.text,
        fontSize: 28,
        fontWeight: FontWeight.w500,
        letterSpacing: -.8,
      ),
      labelSmall: const TextStyle(
        color: PrintWatchColors.muted,
        fontFamily: 'monospace',
        fontSize: 11,
        letterSpacing: .8,
      ),
    ),
  );
}
