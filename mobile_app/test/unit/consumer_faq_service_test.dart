import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/services/consumer_faq_service.dart';
import 'package:petty/src/models/faq_models.dart';

void main() {
  group('ConsumerFaqService', () {
    late ConsumerFaqService service;

    setUp(() {
      service = ConsumerFaqService();
      service.clearCache(); // Start with clean cache
    });

    group('FAQ Parsing', () {
      test('should parse FAQ table correctly', () {
        const mockMarkdown = '''
# Consumer Overview

## 9. FAQ

| Question | Answer |
|----------|--------|
| What hardware is required? | Any BLE/WiFi collar sensor producing periodic motion/aux metrics; simulator provided. |
| Can I run without AWS? | Yes—local mode with moto & in-memory stores for test/dev. |
| Who owns the data? | You do—MIT license & self-hosting mean full control. |

## Other Section
Some other content.
''';

        final sections = service.parseMarkdownContent(mockMarkdown);
        final faqSection = sections.firstWhere((s) => s.title.contains('FAQ'));
        
        expect(faqSection.faqItems.length, equals(3));
        expect(faqSection.faqItems[0].question, equals('What hardware is required?'));
        expect(faqSection.faqItems[0].answer, 
               equals('Any BLE/WiFi collar sensor producing periodic motion/aux metrics; simulator provided.'));
        expect(faqSection.faqItems[1].question, equals('Can I run without AWS?'));
        expect(faqSection.faqItems[2].question, equals('Who owns the data?'));
      });

      test('should handle sections without FAQ items', () {
        const mockMarkdown = '''
# Consumer Overview

## 1. What Is Petty?
Petty is an open, extensible system for pet monitoring.

## 2. Core Benefits
Some benefits here.
''';

        final sections = service.parseMarkdownContent(mockMarkdown);
        
        expect(sections.length, equals(2));
        expect(sections[0].title, equals('1. What Is Petty?'));
        expect(sections[0].faqItems.isEmpty, isTrue);
        expect(sections[0].content.contains('Petty is an open, extensible'), isTrue);
      });

      test('should skip malformed FAQ rows', () {
        const mockMarkdown = '''
## 9. FAQ

| Question | Answer |
|----------|--------|
| Valid question? | Valid answer. |
| Malformed row with only one column |
| Another valid? | Another valid answer. |
''';

        final sections = service.parseMarkdownContent(mockMarkdown);
        final faqSection = sections.first;
        
        expect(faqSection.faqItems.length, equals(2));
        expect(faqSection.faqItems[0].question, equals('Valid question?'));
        expect(faqSection.faqItems[1].question, equals('Another valid?'));
      });
    });

    group('FaqItem', () {
      test('should parse valid markdown table row', () {
        const row = '| What hardware is required? | Any BLE/WiFi collar sensor |';
        final item = FaqItem.fromMarkdownRow(row);
        
        expect(item.question, equals('What hardware is required?'));
        expect(item.answer, equals('Any BLE/WiFi collar sensor'));
      });

      test('should throw FormatException for invalid row', () {
        const row = '| Only one column |';
        
        expect(() => FaqItem.fromMarkdownRow(row), throwsFormatException);
      });

      test('should handle rows with extra columns', () {
        const row = '| Question | Answer | Extra | Column |';
        final item = FaqItem.fromMarkdownRow(row);
        
        expect(item.question, equals('Question'));
        expect(item.answer, equals('Answer'));
      });
    });

    group('Caching', () {
      test('should clear cache when requested', () {
        service.clearCache();
        // We can't directly test private fields, but we can test behavior
        expect(() => service.clearCache(), returnsNormally);
      });
    });
  });
}