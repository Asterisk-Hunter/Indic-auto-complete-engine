import unicodedata

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False
        self.frequency = 0

root = TrieNode()

def _normalize(s: str) -> str:
    return unicodedata.normalize('NFC', s.strip())

def insert(word: str, freq: int = 1):
    word = _normalize(word)
    if not word:
        return
    node = root
    for ch in word:
        if ch not in node.children:
            node.children[ch] = TrieNode()
        node = node.children[ch]
    node.is_word = True
    node.frequency += freq

def load_from_file(path: str):
    count = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            word = parts[0]
            freq = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            insert(word, freq)
            count += 1

def _find_node(prefix: str):
    node = root
    for ch in _normalize(prefix):
        if ch not in node.children:
            return None
        node = node.children[ch]
    return node

def search(word: str) -> bool:
    word = _normalize(word)
    node = _find_node(word)
    return node is not None and node.is_word

def starts_with(prefix: str, max_suggestions: int = 20):
    prefix = _normalize(prefix)
    node = _find_node(prefix)
    if node is None:
        return []

    suggestions = []
    queue = [(node, prefix)]

    while queue and len(suggestions) < 100:
        cur_node, cur_prefix = queue.pop(0)
        if cur_node.is_word:
            suggestions.append((cur_prefix, cur_node.frequency))
        for ch, child in cur_node.children.items():
            queue.append((child, cur_prefix + ch))

    suggestions.sort(key=lambda x: (-x[1], x[0]))
    return [s for s, _ in suggestions[:max_suggestions]]

def fuzzy_search(prefix: str, max_suggestions: int = 10):
    prefix = _normalize(prefix)
    results = set(starts_with(prefix, max_suggestions))
    letters = [chr(i) for i in range(0x0900, 0x097F)]

    for i in range(len(prefix)):
        for l in letters:
            w = prefix[:i] + l + prefix[i+1:]
            results.update(starts_with(w, max_suggestions))

    for i in range(len(prefix)+1):
        for l in letters:
            w = prefix[:i] + l + prefix[i:]
            results.update(starts_with(w, max_suggestions))

    for i in range(len(prefix)):
        w = prefix[:i] + prefix[i+1:]
        results.update(starts_with(w, max_suggestions))

    return list(results)[:max_suggestions]

def levenshtein_distance(s1: str, s2: str) -> int:
    
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    
    if len(s1) == 0:
        return len(s2)
    
    previous_row = list(range(len(s2) + 1))
    
    for i, char1 in enumerate(s1):
        current_row = [i + 1]
        
        for j, char2 in enumerate(s2):
            insertion_cost = current_row[j] + 1
            
            deletion_cost = previous_row[j + 1] + 1
            
            substitution_cost = previous_row[j] + (0 if char1 == char2 else 1)
            
            current_row.append(min(insertion_cost, deletion_cost, substitution_cost))
        
        previous_row = current_row
    
    return previous_row[-1]


def spell_check(word: str, max_distance: int = 2, max_results: int = 10) -> list:
    word = _normalize(word)
    if not word:
        return []
    
    if len(word) < 2:
        return []
    
    candidates = []
    word_len = len(word)
    
    min_len = word_len - max_distance
    max_len = word_len + max_distance
    
    queue = [(root, '', 0)]
    checked = 0
    max_checks = 5000
    
    while queue and checked < max_checks and len(candidates) < max_results * 3:
        node, prefix, depth = queue.pop(0)
        
        if depth > max_len:
            continue
        
        if node.is_word and min_len <= len(prefix) <= max_len:
            distance = levenshtein_distance(word, prefix)
            if distance <= max_distance:
                candidates.append((prefix, distance, node.frequency))
                checked += 1
                
                if len(candidates) >= max_results * 2 and distance <= 1:
                    break
        
        if depth < max_len:
            for char, child in node.children.items():
                queue.append((child, prefix + char, depth + 1))
    
    candidates.sort(key=lambda x: (x[1], -x[2]))
    
    return [w for w, _, _ in candidates[:max_results]]


def autocomplete(prefix: str, max_suggestions: int = 10):
    
    suggestions = starts_with(prefix, max_suggestions)
    
    if not suggestions:
        suggestions = fuzzy_search(prefix, max_suggestions)
    
    if not suggestions:
        suggestions = spell_check(prefix, max_distance=2, max_results=max_suggestions)
    
    return suggestions
