from collections import Counter
import math

class WordAnalytics:
    def __init__(self):
        self.word_freq = Counter()
        self.document_freq = Counter()
        self.total_docs = 0
        self._score_cache = {}
    
    def add_document(self, text: str):
        if not text or not text.strip():
            return
        words = text.lower().split()
        unique_words = set(words)
        for word in unique_words:
            self.document_freq[word] += 1
        for word in words:
            self.word_freq[word] += 1
        self.total_docs += 1
        self._score_cache.clear()
    
    def get_term_frequency(self, word: str) -> int:
        return self.word_freq.get(word.lower(), 0)
    
    def get_document_frequency(self, word: str) -> int:
        return self.document_freq.get(word.lower(), 0)
    
    def get_importance_score(self, word: str) -> float:
        word_lower = word.lower()
        if word_lower in self._score_cache:
            return self._score_cache[word_lower]
        tf = self.word_freq.get(word_lower, 0)
        df = self.document_freq.get(word_lower, 0)
        if tf == 0 or df == 0:
            return 0.0
        idf = math.log((self.total_docs + 1) / (df + 1))
        score = tf * idf
        self._score_cache[word_lower] = score
        return score
    
    def rank_words(self, words: list, top_k: int = None) -> list:
        if not words:
            return []
        scored_words = []
        for word in words:
            score = self.get_importance_score(word)
            scored_words.append((word, score))
        scored_words.sort(key=lambda x: -x[1])
        if top_k:
            return scored_words[:top_k]
        return scored_words
    
    def boost_suggestions(self, suggestions: list) -> list:
        if not suggestions:
            return suggestions
        ranked = self.rank_words(suggestions)
        return [word for word, score in ranked]
    
    def get_common_words(self, top_k: int = 10) -> list:
        return self.word_freq.most_common(top_k)
    
    def get_rare_words(self, top_k: int = 10) -> list:
        sorted_words = sorted(self.document_freq.items(), key=lambda x: x[1])
        return sorted_words[:top_k]
    
    def get_stats(self) -> dict:
        return {
            'total_documents': self.total_docs,
            'unique_words': len(self.word_freq),
            'total_word_occurrences': sum(self.word_freq.values()),
            'avg_words_per_document': sum(self.word_freq.values()) / max(self.total_docs, 1)
        }
    
    def clear(self):
        self.word_freq.clear()
        self.document_freq.clear()
        self.total_docs = 0
        self._score_cache.clear()
    
    def load_from_file(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    self.add_document(line)

word_analytics = WordAnalytics()
