import re
from collections import Counter

# Minimal stopword set
STOPWORDS = set([
    'the', 'and', 'a', 'an', 'of', 'to', 'in', 'for', 'on', 'with', 'is', 'it', 'that', 'this', 'i', 'we', 'you',
    'was', 'are', 'be', 'my', 'have', 'has', 'had', 'not', 'but', 'or', 'as', 'by', 'at', 'from'
])


def extract_keywords(text: str, top_n: int = 6):
    if not text:
        return []
    # simple tokenization
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    words = [w for w in words if w not in STOPWORDS]
    counts = Counter(words)

    # also build bigrams to preserve phrases like 'washing machine'
    bigrams = []
    for i in range(len(words) - 1):
        bigrams.append(f"{words[i]} {words[i+1]}")
    bigram_counts = Counter(bigrams)

    # Combine unigrams and bigrams scores (bigrams get higher weight)
    combined = {}
    for w, c in counts.items():
        combined[w] = combined.get(w, 0) + c
    for b, c in bigram_counts.items():
        combined[b] = combined.get(b, 0) + c * 2

    # Ensure urgent and similar single-token flags are included
    if 'urgent' in text.lower():
        combined['urgent'] = combined.get('urgent', 0) + 5

    sorted_items = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    keywords = [k for k, _ in sorted_items[:top_n]]
    return keywords
