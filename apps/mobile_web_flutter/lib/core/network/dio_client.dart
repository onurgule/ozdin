import 'package:dio/dio.dart';

import '../config/env.dart';

Dio createDio({required String sessionId}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: Env.apiBaseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 60),
      headers: {
        if (Env.apiKey.isNotEmpty) 'X-API-Key': Env.apiKey,
        'X-Session-Id': sessionId,
      },
    ),
  );
  return dio;
}
