class EmojiSuggester:
    def __init__(self):
        self.emoji_map = {
            'happy': ['😊', '😄', '🎉', '😁', '☺️'],
            'sad': ['😢', '😞', '💔', '😭', '☹️'],
            'love': ['❤️', '💕', '😍', '💖', '💗'],
            'angry': ['😠', '😡', '💢', '😤'],
            'laugh': ['😂', '🤣', '😆', '😹'],
            'cry': ['😢', '😭', '😿'],
            'excited': ['🎉', '🎊', '🥳', '😆'],
            'tired': ['😴', '😪', '🥱', '💤'],
            'sick': ['🤒', '🤧', '😷', '🤕'],
            'cool': ['😎', '🆒', '👍'],
            'thinking': ['🤔', '💭', '🧐'],
            'surprised': ['😮', '😯', '😲', '🤯'],
            'confused': ['😕', '🤨', '😵'],
            'food': ['🍕', '🍔', '🍜', '🍱', '🍽️'],
            'pizza': ['🍕', '🍴'],
            'burger': ['🍔', '🍟'],
            'coffee': ['☕', '🍵'],
            'tea': ['🍵', '☕'],
            'cake': ['🎂', '🍰', '🧁'],
            'ice': ['🍦', '🍨', '🧊'],
            'water': ['💧', '💦', '🌊'],
            'beer': ['🍺', '🍻'],
            'wine': ['🍷', '🍾'],
            'fruit': ['🍎', '🍊', '🍌', '🍇'],
            'rice': ['🍚', '🍛'],
            'bread': ['🍞', '🥖', '🥐'],
            'party': ['🎉', '🎊', '🥳', '🍾'],
            'celebrate': ['🎉', '🎊', '🥳'],
            'work': ['💼', '👔', '💻', '📊'],
            'study': ['📚', '📖', '✏️', '📝'],
            'sleep': ['😴', '💤', '🛌'],
            'travel': ['✈️', '🗺️', '🧳', '🌍'],
            'music': ['🎵', '🎶', '🎸', '🎤'],
            'dance': ['💃', '🕺', '🎶'],
            'run': ['🏃', '👟', '💨'],
            'gym': ['💪', '🏋️', '🏃'],
            'game': ['🎮', '🕹️', '🎯'],
            'sun': ['☀️', '🌞', '🌅'],
            'moon': ['🌙', '🌛', '🌜'],
            'star': ['⭐', '✨', '🌟'],
            'rain': ['🌧️', '☔', '💧'],
            'snow': ['❄️', '⛄', '🌨️'],
            'cloud': ['☁️', '⛅', '🌤️'],
            'fire': ['🔥', '🔆'],
            'tree': ['🌳', '🌲', '🌴'],
            'flower': ['🌸', '🌺', '🌻', '🌹'],
            'plant': ['🌱', '🌿', '🍀'],
            'dog': ['🐕', '🐶', '🦴'],
            'cat': ['🐱', '🐈', '😺'],
            'bird': ['🐦', '🦜', '🦅'],
            'fish': ['🐟', '🐠', '🎣'],
            'monkey': ['🐵', '🐒'],
            'lion': ['🦁', '🐯'],
            'elephant': ['🐘'],
            'cow': ['🐄', '🐮'],
            'phone': ['📱', '📞', '☎️'],
            'computer': ['💻', '🖥️', '⌨️'],
            'book': ['📚', '📖', '📕'],
            'car': ['🚗', '🚙', '🏎️'],
            'home': ['🏠', '🏡', '🏘️'],
            'money': ['💰', '💵', '💸', '💳'],
            'gift': ['🎁', '🎀'],
            'heart': ['❤️', '💕', '💖', '💗'],
            'star': ['⭐', '✨', '🌟'],
            'fire': ['🔥', '🔆'],
            'check': ['✅', '✓', '☑️'],
            'time': ['⏰', '⏱️', '⌚'],
            'yes': ['👍', '✅', '👌'],
            'no': ['👎', '❌', '🚫'],
            'ok': ['👌', '✅', '👍'],
            'stop': ['✋', '🛑', '⛔'],
            'clap': ['👏', '🎉'],
            'wave': ['👋', '🖐️'],
            'pray': ['🙏', '🕉️'],
            'morning': ['🌅', '☀️', '🌄'],
            'night': ['🌙', '🌃', '⭐'],
            'birthday': ['🎂', '🎉', '🎁', '🥳'],
            'new': ['🆕', '✨', '🌟'],
            'year': ['🎊', '🎉', '🥂'],
            'good': ['👍', '✅', '👌', '😊'],
            'bad': ['👎', '❌', '😞'],
            'hello': ['👋', '😊', '🙋'],
            'bye': ['👋', '😢'],
            'thanks': ['🙏', '😊'],
            'welcome': ['👋', '🙏'],
            'sorry': ['😞', '🙏'],
            'please': ['🙏'],
        }
        self._normalize_map()
    
    def _normalize_map(self):
        normalized = {}
        for key, value in self.emoji_map.items():
            normalized[key.lower()] = value
        self.emoji_map = normalized
    
    def suggest(self, word: str, top_k: int = 3) -> list:
        if not word:
            return []
        word_lower = word.lower().strip()
        if word_lower in self.emoji_map:
            return self.emoji_map[word_lower][:top_k]
        matches = []
        for key, emojis in self.emoji_map.items():
            if key in word_lower or word_lower in key:
                matches.extend(emojis)
        seen = set()
        unique_matches = []
        for emoji in matches:
            if emoji not in seen:
                seen.add(emoji)
                unique_matches.append(emoji)
        return unique_matches[:top_k]
    
    def suggest_for_phrase(self, phrase: str, top_k: int = 5) -> list:
        if not phrase:
            return []
        words = phrase.lower().split()
        all_suggestions = []
        for word in words:
            suggestions = self.suggest(word, top_k=3)
            all_suggestions.extend(suggestions)
        seen = set()
        unique = []
        for emoji in all_suggestions:
            if emoji not in seen:
                seen.add(emoji)
                unique.append(emoji)
        return unique[:top_k]
    
    def add_mapping(self, word: str, emojis: list):
        if word and emojis:
            self.emoji_map[word.lower()] = emojis
    
    def get_all_categories(self) -> list:
        return sorted(list(self.emoji_map.keys()))
    
    def get_random_emoji(self, category: str = None) -> str:
        import random
        if category and category.lower() in self.emoji_map:
            emojis = self.emoji_map[category.lower()]
            return random.choice(emojis) if emojis else ''
        all_emojis = []
        for emojis in self.emoji_map.values():
            all_emojis.extend(emojis)
        return random.choice(all_emojis) if all_emojis else ''

emoji_suggester = EmojiSuggester()
