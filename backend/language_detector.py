class LanguageDetector:
    
    
    def __init__(self):
        self.unicode_ranges = {
            'english': (0x0041, 0x007A),
            'hindi': (0x0900, 0x097F),
            'tamil': (0x0B80, 0x0BFF),
            'malayalam': (0x0D00, 0x0D7F),
            'telugu': (0x0C00, 0x0C7F),
        }
    
    def detect(self, text: str) -> str:
        
        if not text or not text.strip():
            return 'english'
        
        char_counts = {lang: 0 for lang in self.unicode_ranges}
        
        for char in text:
            code = ord(char)
            
            for lang, (start, end) in self.unicode_ranges.items():
                if start <= code <= end:
                    char_counts[lang] += 1
                    break
        
        detected_lang = max(char_counts.items(), key=lambda x: x[1])
        
        if detected_lang[1] == 0:
            return 'english'
        
        return detected_lang[0]
    
    def detect_with_confidence(self, text: str) -> dict:
        
        if not text or not text.strip():
            return {'english': 100.0}
        
        char_counts = {lang: 0 for lang in self.unicode_ranges}
        total_chars = 0
        
        for char in text:
            code = ord(char)
            
            for lang, (start, end) in self.unicode_ranges.items():
                if start <= code <= end:
                    char_counts[lang] += 1
                    total_chars += 1
                    break
        
        if total_chars == 0:
            return {'english': 100.0}
        
        confidence = {}
        for lang, count in char_counts.items():
            percentage = (count / total_chars) * 100
            if percentage > 0:
                confidence[lang] = round(percentage, 2)
        
        confidence = dict(sorted(confidence.items(), key=lambda x: -x[1]))
        
        return confidence if confidence else {'english': 100.0}
    
    def is_multilingual(self, text: str, threshold: float = 20.0) -> bool:
        
        confidence = self.detect_with_confidence(text)
        
        languages_above_threshold = sum(1 for score in confidence.values() if score >= threshold)
        
        return languages_above_threshold > 1
    
    def get_supported_languages(self) -> list:
        
        return list(self.unicode_ranges.keys())


language_detector = LanguageDetector()
