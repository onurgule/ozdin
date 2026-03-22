import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:yasar_nuri/app.dart';

void main() {
  testWidgets('Chat intro visible', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: YasarNuriApp()));
    await tester.pumpAndSettle();
    expect(find.textContaining('kaynaklara dayalı'), findsOneWidget);
  });
}
