class FaqItem {
  final String question;
  final String answer;

  const FaqItem({
    required this.question,
    required this.answer,
  });

  factory FaqItem.fromMarkdownRow(String row) {
    final columns = row.split('|').map((e) => e.trim()).toList();
    if (columns.length >= 3) {
      return FaqItem(
        question: columns[1],
        answer: columns[2],
      );
    }
    throw FormatException('Invalid FAQ row format: $row');
  }
}

class HelpSection {
  final String title;
  final String content;
  final List<FaqItem> faqItems;

  const HelpSection({
    required this.title,
    required this.content,
    this.faqItems = const [],
  });
}