import 'package:dio/dio.dart';

import 'models.dart';

class ChatRepository {
  ChatRepository(this._dio, {required this.sessionId});

  final Dio _dio;
  final String sessionId;

  Future<ChatAskResponseDto> ask(String question) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/v1/chat/ask',
      data: {
        'question': question,
        'answer_language': 'tr',
        'session_id': sessionId,
      },
    );
    final data = res.data;
    if (data == null) {
      throw StateError('Boş yanıt');
    }
    return ChatAskResponseDto.fromJson(data);
  }
}
