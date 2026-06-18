class Book {
  final String bookId;
  final String bookName;
  final String author;
  final int wordCount;
  final String status;
  final String category;
  final String abstract;
  final String thumbUrl;

  const Book({
    required this.bookId,
    required this.bookName,
    required this.author,
    required this.wordCount,
    required this.status,
    required this.category,
    required this.abstract,
    required this.thumbUrl,
  });

  factory Book.fromJson(Map<String, dynamic> json) {
    return Book(
      bookId: json['book_id'] as String? ?? '',
      bookName: json['book_name'] as String? ?? '未知',
      author: json['author'] as String? ?? '未知',
      wordCount: (json['word_count'] as num?)?.toInt() ?? 0,
      status: json['status'] as String? ?? '未知',
      category: json['category'] as String? ?? '',
      abstract: json['abstract'] as String? ?? '',
      thumbUrl: json['thumb_url'] as String? ?? '',
    );
  }

  String get wordCountText {
    if (wordCount >= 10000) {
      return '${(wordCount / 10000).toStringAsFixed(1)}万字';
    }
    return '$wordCount字';
  }

  bool get isCompleted => status == '已完结';
}
