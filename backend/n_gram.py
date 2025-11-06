from collections import defaultdict, Counter

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def autocomplete(self, prefix: str, limit: int = 5):
        
        results = []
        node = self.root

        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]

        def dfs(curr, path):
            if len(results) >= limit:
                return
            if curr.is_end:
                results.append(path)
            for ch in curr.children:
                dfs(curr.children[ch], path + ch)

        dfs(node, prefix)
        return results

class NGramModel:
    def __init__(self):
        self.model = defaultdict(lambda: defaultdict(int))
        self.trie = Trie()
        self.total_pairs = 0

    def load_from_file(self, path: str):
        count = 0
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    prev_word, next_word, freq = parts[0], parts[1], int(parts[2])
                elif len(parts) == 2:
                    prev_word, next_word, freq = parts[0], parts[1], 1
                else:
                    continue

                self.model[prev_word][next_word] += freq
                self.trie.insert(next_word)
                count += 1

        self.total_pairs = count

    def predict_next_word(self, prev_word: str, top_k: int = 5):
        
        if prev_word not in self.model:
            return []
        next_words = self.model[prev_word]
        counter = Counter(next_words)
        return [w for w, _ in counter.most_common(top_k)]

    def predict_prefix(self, prefix: str, top_k: int = 5):
        
        return self.trie.autocomplete(prefix, limit=top_k)

    # Trigram support removed from the model.
    
    
    def hybrid_predict(self, user_input: str, top_k: int = 5):
        
        words = user_input.strip().split()
        if not words:
            return []

        if len(words) == 1:
            prefix = words[0]
            
            preds = self.predict_next_word(prefix, top_k)
            if preds:
                return preds
            else:
                return self.predict_prefix(prefix, top_k)

        if len(words) >= 2:
            word1 = words[-2]
            word2 = words[-1]
            # Trigram lookup removed — fall through to bigram/prefix predictors.
        
        prev_word = words[-2] if len(words) >= 2 else words[-1]
        prefix = words[-1]

        next_candidates = self.predict_next_word(prev_word, top_k)
        prefix_candidates = self.predict_prefix(prefix, top_k)

        combined = list(dict.fromkeys(next_candidates + prefix_candidates))
        return combined[:top_k]
    
    # Trigram loader removed — trigram feature deprecated.
    
    # Phrase-related loader removed; feature deprecated.

ngram = NGramModel()

def load_from_file(path: str):
    
    ngram.load_from_file(path)
def predict_next_word(prev_word: str, top_k: int = 5):
    
    return ngram.predict_next_word(prev_word, top_k)

def predict_prefix(prefix: str, top_k: int = 5):
    
    return ngram.predict_prefix(prefix, top_k)

# Trigram wrappers removed — feature deprecated.
def hybrid_predict(user_input: str, top_k: int = 5):
    
    return ngram.hybrid_predict(user_input, top_k)
