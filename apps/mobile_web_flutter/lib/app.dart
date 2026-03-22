import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'features/chat/presentation/chat_screen.dart';

final _router = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (context, state) => const ChatScreen()),
  ],
);

class YasarNuriApp extends ConsumerWidget {
  const YasarNuriApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textTheme = const TextTheme(
      bodyLarge: TextStyle(fontSize: 18, height: 1.35),
      bodyMedium: TextStyle(fontSize: 17, height: 1.35),
      titleMedium: TextStyle(fontSize: 18, fontWeight: FontWeight.w500, height: 1.35),
    );
    final base = ThemeData(
      useMaterial3: true,
      colorSchemeSeed: const Color(0xFF1B5E20),
      textTheme: textTheme,
    );
    return MaterialApp.router(
      title: 'Ozdin: Dini Yapay Zeka',
      theme: base,
      darkTheme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF81C784),
        brightness: Brightness.dark,
        textTheme: textTheme,
      ),
      themeMode: ThemeMode.system,
      routerConfig: _router,
    );
  }
}
