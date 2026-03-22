import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../core/network/dio_client.dart';
import '../data/chat_repository.dart';

final sessionIdProvider = Provider<String>((ref) => const Uuid().v4());

final dioProvider = Provider<Dio>((ref) {
  final sid = ref.watch(sessionIdProvider);
  return createDio(sessionId: sid);
});

final chatRepositoryProvider = Provider<ChatRepository>((ref) {
  return ChatRepository(
    ref.watch(dioProvider),
    sessionId: ref.watch(sessionIdProvider),
  );
});
