from collections import Counter, defaultdict
import json
import os

class UserModel:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.personal_vocab = Counter()
        self.personal_bigrams = defaultdict(lambda: defaultdict(int))
        self.recent_words = []
        self.max_recent = 50
        self.total_interactions = 0
    
    def learn(self, text: str):
        if not text or not text.strip():
            return
        
        words = text.lower().split()
        
        for word in words:
            self.personal_vocab[word] += 1
            
            if word in self.recent_words:
                self.recent_words.remove(word)
            self.recent_words.insert(0, word)
            if len(self.recent_words) > self.max_recent:
                self.recent_words.pop()
        
        for i in range(len(words) - 1):
            self.personal_bigrams[words[i]][words[i+1]] += 1
        
        self.total_interactions += 1
    
    def get_personalized_suggestions(self, base_suggestions: list, boost_factor: float = 2.0) -> list:
        if not base_suggestions:
            return base_suggestions
        
        scored = []
        for word in base_suggestions:
            word_lower = word.lower()
            frequency_score = self.personal_vocab.get(word_lower, 0)
            
            recency_score = 0
            if word_lower in self.recent_words:
                position = self.recent_words.index(word_lower)
                recency_score = (self.max_recent - position) / self.max_recent
            
            total_score = (frequency_score * boost_factor) + recency_score
            scored.append((word, total_score))
        
        scored.sort(key=lambda x: -x[1])
        return [word for word, score in scored]
    
    def predict_next_word(self, prev_word: str, top_k: int = 5) -> list:
        prev_word_lower = prev_word.lower()
        
        if prev_word_lower not in self.personal_bigrams:
            return []
        
        next_words = self.personal_bigrams[prev_word_lower]
        counter = Counter(next_words)
        return [w for w, _ in counter.most_common(top_k)]
    
    def get_favorite_words(self, top_k: int = 10) -> list:
        return self.personal_vocab.most_common(top_k)
    
    def get_stats(self) -> dict:
        return {
            'user_id': self.user_id,
            'total_interactions': self.total_interactions,
            'unique_words': len(self.personal_vocab),
            'total_words': sum(self.personal_vocab.values()),
            'favorite_words': self.get_favorite_words(5)
        }
    
    def save_to_file(self, directory: str = 'user_data'):
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f'{self.user_id}.json')
        
        bigrams_dict = {
            k: dict(v) for k, v in self.personal_bigrams.items()
        }
        
        data = {
            'user_id': self.user_id,
            'personal_vocab': dict(self.personal_vocab),
            'personal_bigrams': bigrams_dict,
            'recent_words': self.recent_words,
            'total_interactions': self.total_interactions
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved user model for {self.user_id}")
        except Exception as e:
            print(f"Error saving user model: {e}")
    
    def load_from_file(self, directory: str = 'user_data'):
        filepath = os.path.join(directory, f'{self.user_id}.json')
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.personal_vocab = Counter(data.get('personal_vocab', {}))
            
            bigrams_data = data.get('personal_bigrams', {})
            self.personal_bigrams = defaultdict(lambda: defaultdict(int))
            for k, v in bigrams_data.items():
                for next_word, count in v.items():
                    self.personal_bigrams[k][next_word] = count
            
            self.recent_words = data.get('recent_words', [])
            self.total_interactions = data.get('total_interactions', 0)
            
            print(f"Loaded user model for {self.user_id}")
            return True
        except FileNotFoundError:
            print(f"No saved data found for user {self.user_id}")
            return False
        except Exception as e:
            print(f"Error loading user model: {e}")
            return False
    
    def clear_history(self):
        self.personal_vocab.clear()
        self.personal_bigrams.clear()
        self.recent_words.clear()
        self.total_interactions = 0


class PersonalizationManager:
    def __init__(self, storage_dir: str = 'user_data'):
        self.users = {}
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def get_user(self, user_id: str) -> UserModel:
        if user_id in self.users:
            return self.users[user_id]
        
        user_model = UserModel(user_id)
        user_model.load_from_file(self.storage_dir)
        self.users[user_id] = user_model
        return user_model
    
    def save_user(self, user_id: str):
        if user_id in self.users:
            self.users[user_id].save_to_file(self.storage_dir)
    
    def save_all_users(self):
        for user_id, user_model in self.users.items():
            user_model.save_to_file(self.storage_dir)
    
    def delete_user(self, user_id: str):
        if user_id in self.users:
            del self.users[user_id]
        
        filepath = os.path.join(self.storage_dir, f'{user_id}.json')
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted user data for {user_id}")
        except Exception as e:
            print(f"Error deleting user data: {e}")
    
    def get_all_user_ids(self) -> list:
        try:
            files = os.listdir(self.storage_dir)
            user_ids = [f[:-5] for f in files if f.endswith('.json')]
            return user_ids
        except Exception as e:
            print(f"Error listing users: {e}")
            return []


personalization_manager = PersonalizationManager()
