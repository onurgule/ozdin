import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../data/models.dart';
import '../providers/chat_providers.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _controller = TextEditingController();
  final _scroll = ScrollController();
  final List<UiMessage> _messages = [];
  bool _loading = false;
  bool _offline = false;
  final _speech = stt.SpeechToText();
  bool _speechAvailable = false;
  final _tts = FlutterTts();

  @override
  void initState() {
    super.initState();
    _bootstrapSpeech();
    _bootstrapConnectivity();
    _messages.add(
      UiMessage(
        role: MessageRole.assistant,
        text:
            'Burada yalnızca belirtilen kaynaklara dayalı cevaplar verilir. Sorunuzu yazabilir veya mikrofonu kullanabilirsiniz.',
      ),
    );
  }

  Future<void> _bootstrapConnectivity() async {
    final api = Connectivity();
    final r = await api.checkConnectivity();
    if (!mounted) return;
    setState(() {
      _offline = r.contains(ConnectivityResult.none);
    });
    api.onConnectivityChanged.listen((List<ConnectivityResult> result) {
      if (!mounted) return;
      setState(() => _offline = result.contains(ConnectivityResult.none));
    });
  }

  Future<void> _bootstrapSpeech() async {
    try {
      final ok = await _speech.initialize();
      if (!mounted) return;
      setState(() => _speechAvailable = ok);
    } catch (_) {
      setState(() => _speechAvailable = false);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _send(String text) async {
    final q = text.trim();
    if (q.isEmpty || _loading) return;
    setState(() {
      _messages.add(UiMessage(role: MessageRole.user, text: q));
      _messages.add(UiMessage(role: MessageRole.assistant, text: '', loading: true));
      _loading = true;
    });
    _controller.clear();
    _scrollToEnd();

    try {
      final repo = ref.read(chatRepositoryProvider);
      final res = await repo.ask(q);
      setState(() {
        _messages.removeLast();
        _messages.add(
          UiMessage(
            role: MessageRole.assistant,
            text: res.answer,
            citations: res.citations,
          ),
        );
        _loading = false;
      });
    } on DioException catch (e) {
      setState(() {
        _messages.removeLast();
        _messages.add(
          UiMessage(
            role: MessageRole.assistant,
            text:
                'Bağlantı kurulamadı. İnternetinizi kontrol edip yeniden deneyin. (${e.message ?? "hata"})',
          ),
        );
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _messages.removeLast();
        _messages.add(
          UiMessage(
            role: MessageRole.assistant,
            text: 'Bir sorun oluştu. Lütfen yeniden deneyin.',
          ),
        );
        _loading = false;
      });
    }
    _scrollToEnd();
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scroll.hasClients) return;
      _scroll.animateTo(
        _scroll.position.maxScrollExtent + 120,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _mic() async {
    if (!_speechAvailable) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Bu cihazda sesli giriş kullanılamıyor; yazarak sorabilirsiniz.')),
      );
      return;
    }
    await _speech.listen(
      onResult: (r) {
        _controller.text = r.recognizedWords;
      },
    );
  }

  Future<void> _readAloud(String text) async {
    await _tts.setLanguage('tr-TR');
    await _tts.speak(text);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Semantics(
          label: 'Ozdin: Dini Yapay Zeka',
          child: const Text('Ozdin'),
        ),
        actions: [
          IconButton(
            tooltip: 'Bilgi',
            icon: const Icon(Icons.info_outline),
            onPressed: () => context.pushInfo(),
          ),
        ],
      ),
      body: Column(
        children: [
          if (_offline)
            MaterialBanner(
              content: const Text('Çevrimdışı görünüyorsunuz.'),
              actions: [
                TextButton(onPressed: () => setState(() => _offline = false), child: const Text('Tamam')),
              ],
            ),
          Expanded(
            child: ListView.builder(
              controller: _scroll,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              itemCount: _messages.length,
              itemBuilder: (context, i) {
                final m = _messages[i];
                return _Bubble(
                  message: m,
                  onSpeak: m.role == MessageRole.assistant && m.text.isNotEmpty ? () => _readAloud(m.text) : null,
                );
              },
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Column(
                children: [
                  Center(
                    child: Semantics(
                      button: true,
                      label: 'Sesle sor',
                      child: SizedBox(
                        width: 88,
                        height: 88,
                        child: FilledButton(
                          onPressed: _loading ? null : _mic,
                          style: FilledButton.styleFrom(
                            shape: const CircleBorder(),
                            padding: const EdgeInsets.all(20),
                          ),
                          child: Icon(Icons.mic, size: 40, color: theme.colorScheme.onPrimary),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _controller,
                    minLines: 2,
                    maxLines: 5,
                    textInputAction: TextInputAction.send,
                    style: theme.textTheme.titleMedium,
                    decoration: const InputDecoration(
                      hintText: 'Sorunuzu buraya yazın…',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _send(_controller.text),
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: FilledButton(
                      onPressed: _loading ? null : () => _send(_controller.text),
                      child: _loading
                          ? const SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Text('Gönder', style: TextStyle(fontSize: 18)),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

extension on BuildContext {
  void pushInfo() {
    showModalBottomSheet<void>(
      context: this,
      showDragHandle: true,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Bilgi', style: Theme.of(ctx).textTheme.titleLarge),
            const SizedBox(height: 12),
            const Text(
              'Bu uygulama yalnızca Yaşar Nuri Öztürk kaynaklarından cevap verir. Genel bilgi veya internet kullanılmaz.',
            ),
            const SizedBox(height: 16),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Kapat')),
            ),
          ],
        ),
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.message, this.onSpeak});

  final UiMessage message;
  final VoidCallback? onSpeak;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUser = message.role == MessageRole.user;
    final bg = isUser ? theme.colorScheme.primaryContainer : theme.colorScheme.surfaceContainerHighest;
    final fg = isUser ? theme.colorScheme.onPrimaryContainer : theme.colorScheme.onSurfaceVariant;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Align(
        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Column(
            crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
            children: [
              Semantics(
                label: isUser ? 'Sizin mesajınız' : 'Yanıt',
                child: DecoratedBox(
                  decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(16)),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: message.loading
                        ? const SizedBox(
                            width: 28,
                            height: 28,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Text(
                            message.text,
                            style: theme.textTheme.titleMedium?.copyWith(color: fg, height: 1.35),
                          ),
                  ),
                ),
              ),
              if (onSpeak != null)
                TextButton.icon(
                  onPressed: onSpeak,
                  icon: const Icon(Icons.volume_up),
                  label: const Text('Sesli oku'),
                ),
              if (message.citations.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text('Kaynaklar', style: theme.textTheme.titleSmall),
                const SizedBox(height: 6),
                ...message.citations.map((c) => _CitationCard(citation: c)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _CitationCard extends StatelessWidget {
  const _CitationCard({required this.citation});

  final CitationDto citation;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final parts = <String>[
      citation.bookTitle,
      if (citation.sectionTitle != null) citation.sectionTitle!,
      if (citation.pageNumber != null) 's. ${citation.pageNumber}',
      if (citation.surahName != null) citation.surahName!,
      if (citation.ayahStart != null) '${citation.ayahStart}',
    ];
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Semantics(
          label: 'Kaynak kartı',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(parts.join(' · '), style: theme.textTheme.bodyLarge),
              if (citation.questionText != null && citation.questionText!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    citation.questionText!,
                    style: theme.textTheme.bodyMedium,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
