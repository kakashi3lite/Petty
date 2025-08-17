import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/faq_models.dart';

/// Service for parsing FAQ content from CONSUMER_OVERVIEW.md with caching
class ConsumerFaqService {
  static const String _documentUrl = 
    'https://raw.githubusercontent.com/kakashi3lite/Petty/main/docs/CONSUMER_OVERVIEW.md';
  
  static List<HelpSection>? _cachedSections;
  static DateTime? _lastCacheTime;
  static const Duration _cacheExpiry = Duration(hours: 6);

  /// Get FAQ sections with caching
  Future<List<HelpSection>> getFaqSections() async {
    // Return cached data if still valid
    if (_cachedSections != null && 
        _lastCacheTime != null &&
        DateTime.now().difference(_lastCacheTime!) < _cacheExpiry) {
      return _cachedSections!;
    }

    try {
      final response = await http.get(Uri.parse(_documentUrl));
      if (response.statusCode == 200) {
        final content = utf8.decode(response.bodyBytes);
        final sections = parseMarkdownContent(content);
        
        // Cache the result
        _cachedSections = sections;
        _lastCacheTime = DateTime.now();
        
        return sections;
      } else {
        throw Exception('Failed to load consumer overview: ${response.statusCode}');
      }
    } catch (e) {
      // Return cached data if available, even if expired
      if (_cachedSections != null) {
        return _cachedSections!;
      }
      rethrow;
    }
  }

  /// Clear cache (useful for refresh functionality)
  void clearCache() {
    _cachedSections = null;
    _lastCacheTime = null;
  }

  List<HelpSection> parseMarkdownContent(String content) {
    final lines = content.split('\n');
    final sections = <HelpSection>[];
    
    String? currentTitle;
    final currentContent = StringBuffer();
    final currentFaqItems = <FaqItem>[];
    bool inFaqTable = false;
    
    for (int i = 0; i < lines.length; i++) {
      final line = lines[i].trim();
      
      // Detect headings
      if (line.startsWith('## ')) {
        // Save previous section if exists
        if (currentTitle != null) {
          sections.add(HelpSection(
            title: currentTitle,
            content: currentContent.toString().trim(),
            faqItems: List.from(currentFaqItems),
          ));
        }
        
        // Start new section
        currentTitle = line.replaceFirst('## ', '').trim();
        currentContent.clear();
        currentFaqItems.clear();
        inFaqTable = false;
        continue;
      }
      
      // Detect FAQ table
      if (currentTitle == '9. FAQ' || currentTitle?.contains('FAQ') == true) {
        if (line.startsWith('|') && line.contains('Question') && line.contains('Answer')) {
          inFaqTable = true;
          continue; // Skip header row
        }
        if (line.startsWith('|') && line.contains('---')) {
          continue; // Skip separator row
        }
        if (line.startsWith('|') && inFaqTable) {
          try {
            final faqItem = FaqItem.fromMarkdownRow(line);
            if (faqItem.question.isNotEmpty && faqItem.answer.isNotEmpty) {
              currentFaqItems.add(faqItem);
            }
          } catch (e) {
            // Skip malformed rows
            continue;
          }
          continue;
        }
        if (!line.startsWith('|')) {
          inFaqTable = false;
        }
      }
      
      // Add to content if not in FAQ table
      if (!inFaqTable) {
        currentContent.writeln(line);
      }
    }
    
    // Add final section
    if (currentTitle != null) {
      sections.add(HelpSection(
        title: currentTitle,
        content: currentContent.toString().trim(),
        faqItems: List.from(currentFaqItems),
      ));
    }
    
    return sections;
  }
}