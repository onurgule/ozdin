class ChatAskResponseDto {
  ChatAskResponseDto({
    required this.answer,
    required this.found,
    required this.confidence,
    required this.citations,
    this.disclaimer,
  });

  final String answer;
  final bool found;
  final double confidence;
  final List<CitationDto> citations;
  final String? disclaimer;

  factory ChatAskResponseDto.fromJson(Map<String, dynamic> json) {
    final raw = json['citations'] as List<dynamic>? ?? [];
    return ChatAskResponseDto(
      answer: json['answer'] as String? ?? '',
      found: json['found'] as bool? ?? false,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
      citations: raw
          .map((e) => CitationDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      disclaimer: json['disclaimer'] as String?,
    );
  }
}

class CitationDto {
  CitationDto({
    required this.chunkId,
    required this.bookTitle,
    this.sectionTitle,
    this.pageNumber,
    this.surahName,
    this.ayahStart,
    this.ayahEnd,
    this.questionText,
  });

  final String chunkId;
  final String bookTitle;
  final String? sectionTitle;
  final int? pageNumber;
  final String? surahName;
  final int? ayahStart;
  final int? ayahEnd;
  final String? questionText;

  factory CitationDto.fromJson(Map<String, dynamic> json) {
    return CitationDto(
      chunkId: json['chunk_id'] as String? ?? '',
      bookTitle: json['book_title'] as String? ?? '',
      sectionTitle: json['section_title'] as String?,
      pageNumber: json['page_number'] as int?,
      surahName: json['surah_name'] as String?,
      ayahStart: json['ayah_start'] as int?,
      ayahEnd: json['ayah_end'] as int?,
      questionText: json['question_text'] as String?,
    );
  }
}

enum MessageRole { user, assistant }

class UiMessage {
  UiMessage({
    required this.role,
    required this.text,
    this.citations = const [],
    this.loading = false,
  });

  final MessageRole role;
  final String text;
  final List<CitationDto> citations;
  final bool loading;
}
