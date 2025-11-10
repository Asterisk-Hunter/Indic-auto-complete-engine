import os

class ContentFilter:
    def __init__(self):
        self.blocklist = set()
        self.blocklist_loaded = False
    
    def load_blocklist(self, path: str = None):
        if path is None:
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, 'datasets', 'nsfw_words.txt')
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    self.blocklist.add(word)
        self.blocklist_loaded = True
    
    def is_blocked(self, word: str) -> bool:
        if not word:
            return False
        word_lower = word.lower()
        
        # Check exact match first
        if word_lower in self.blocklist:
            return True
        
        # Check if any blocked word is a substring of the input word
        # This catches variations like "fucked", "fucker", etc.
        for blocked_word in self.blocklist:
            if blocked_word in word_lower:
                return True
        
        return False
    
    def filter_suggestions(self, suggestions: list) -> list:
        if not self.blocklist_loaded or not suggestions:
            return suggestions
        return [word for word in suggestions if not self.is_blocked(word)]
    
    def add_to_blocklist(self, word: str):
        if word:
            self.blocklist.add(word.lower())
    
    def remove_from_blocklist(self, word: str):
        if word:
            self.blocklist.discard(word.lower())
    
    def get_blocklist_size(self) -> int:
        return len(self.blocklist)

content_filter = ContentFilter()
