# Indic Autocomplete Engine - Technical Documentation for Academic Review

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Design Decisions](#architecture--design-decisions)
3. [Core Data Structures](#core-data-structures)
4. [Backend Components Deep Dive](#backend-components-deep-dive)
5. [Frontend Implementation](#frontend-implementation)
6. [How to Run & Test](#how-to-run--test)
7. [Code Walkthrough](#code-walkthrough)

---

## Project Overview

### What Does This System Do?
This is a multilingual text prediction and autocomplete system supporting **5 Indian languages** (English, Hindi, Malayalam, Tamil, Telugu). It provides:
- **Real-time word completion** as users type
- **Next-word prediction** based on context
- **Personalized suggestions** that learn from individual users
- **Spell checking** with fuzzy matching
- **Emoji suggestions** based on typed words
- **Language detection** for multilingual input

### Key Technologies
- **Backend**: FastAPI (Python) - lightweight, modern REST API
- **Frontend**: React + TypeScript + Vite
- **Data Structures**: Custom Trie, N-gram models, Counters
- **Storage**: JSON files for user personalization

---

## Architecture & Design Decisions

### Why This Architecture?

```
User Types → Frontend (React)
                ↓
         API Request (REST)
                ↓
    Backend (FastAPI) → Trie Autocomplete
                      → N-gram Prediction
                      → Personalization
                      → Content Filter
                ↓
         Ranked Results
                ↓
         Frontend Display
```

**Design Choices:**
1. **Separation of Concerns**: Backend handles all language processing; frontend focuses on UI
2. **Stateless API**: Each request is independent (RESTful design)
3. **Caching**: LRU cache for frequently requested suggestions (reduces computation)
4. **Modular Components**: Each feature (trie, n-gram, personalization) is a separate module

---

## Core Data Structures

### 1. Trie (Prefix Tree)

#### What is a Trie?
A Trie is a tree-like data structure where each node represents a single character. Words are stored by following paths from the root to leaf nodes.

**Example:**
```
If we insert words: "cat", "car", "card"

Root
 └─ c
     └─ a
         ├─ t (word end: "cat")
         └─ r (word end: "car")
             └─ d (word end: "card")
```

#### Why Use a Trie for Autocomplete?

**Time Complexity:**
- Insert word: O(m) where m = length of word
- Search prefix: O(m) where m = length of prefix
- Autocomplete: O(m + k) where k = number of results

**Advantages:**
1. **Fast prefix matching**: Much faster than linear search through dictionary
2. **Memory efficient**: Common prefixes share nodes
3. **Natural for autocomplete**: Tree structure mirrors how words are typed character-by-character

**Alternative (Why NOT Hash Table?):**
- Hash table requires exact match → can't do prefix search
- Would need O(n) scan of all words to find matches starting with "ca"

#### Our Trie Implementation (`backend/trie.py`)

**Key Components:**

```python
class TrieNode:
    def __init__(self):
        self.children = {}      # Maps char → child TrieNode
        self.is_word = False    # True if this node ends a valid word
        self.frequency = 0      # How common this word is
```

**Why store frequency?**
- Allows ranking suggestions by popularity
- Example: "the" appears more than "thee" → rank "the" higher

**Core Functions:**

1. **`insert(word, freq)`** - Add word to trie
   ```python
   def insert(word: str, freq: int = 1):
       node = root
       for ch in word:
           if ch not in node.children:
               node.children[ch] = TrieNode()
           node = node.children[ch]
       node.is_word = True
       node.frequency += freq
   ```
   - Walks character by character
   - Creates new nodes as needed
   - Marks final node as word end
   - Updates frequency count

2. **`starts_with(prefix, max_suggestions)`** - Find all completions
   ```python
   def starts_with(prefix: str, max_suggestions: int = 20):
       # Step 1: Navigate to prefix node
       node = _find_node(prefix)
       if node is None:
           return []
       
       # Step 2: BFS to collect all words under this prefix
       suggestions = []
       queue = [(node, prefix)]
       
       while queue and len(suggestions) < 100:
           cur_node, cur_prefix = queue.pop(0)
           if cur_node.is_word:
               suggestions.append((cur_prefix, cur_node.frequency))
           for ch, child in cur_node.children.items():
               queue.append((child, cur_prefix + ch))
       
       # Step 3: Sort by frequency (most common first)
       suggestions.sort(key=lambda x: (-x[1], x[0]))
       return [s for s, _ in suggestions[:max_suggestions]]
   ```
   - Uses **Breadth-First Search (BFS)** to explore subtree
   - Collects words with their frequencies
   - Sorts by frequency descending, then alphabetically

3. **`spell_check(word, max_distance)`** - Find similar words
   ```python
   def spell_check(word: str, max_distance: int = 2, max_results: int = 10):
       # Calculate Levenshtein distance to all words in trie
       candidates = []
       for candidate_word, frequency in all_words:
           distance = levenshtein_distance(word, candidate_word)
           if distance <= max_distance:
               candidates.append((candidate_word, distance, frequency))
       
       # Sort by: closest match first, then most frequent
       candidates.sort(key=lambda x: (x[1], -x[2]))
       return [word for word, _, _ in candidates[:max_results]]
   ```

**Levenshtein Distance Algorithm:**
- Measures "edit distance" between two words
- Counts minimum number of insertions, deletions, or substitutions needed
- Example: "cat" → "car" = 1 substitution (t→r)
- Uses **dynamic programming** (2D table) for O(m×n) complexity

**Why Levenshtein for Spell Check?**
- Catches typos: "teh" → "the" (distance 1)
- Handles missing/extra letters: "aplpe" → "apple" (distance 1)
- Better than exact match (users make mistakes!)

---

### 2. N-gram Model (Bigram)

#### What is an N-gram?
An N-gram is a sequence of N consecutive words. A **bigram** (2-gram) tracks pairs of words that appear together.

**Example from dataset:**
```
"the cat" appears 5000 times
"the dog" appears 3000 times
"the house" appears 2000 times
```

When user types "the ", we predict: "cat" (most frequent), "dog", "house"

#### Our N-gram Implementation (`backend/n_gram.py`)

**Data Structure:**
```python
class NGramModel:
    def __init__(self):
        # Nested dict: prev_word → {next_word → count}
        self.model = defaultdict(lambda: defaultdict(int))
        self.trie = Trie()  # For prefix completion
        self.total_pairs = 0
```

**Why nested defaultdict?**
```python
self.model["the"]["cat"] = 5000
self.model["the"]["dog"] = 3000

# Easy lookup:
next_words = self.model["the"]  # {"cat": 5000, "dog": 3000, ...}
```

**Loading Bigrams from File:**
```python
def load_from_file(self, path: str):
    # File format: "prev_word next_word frequency"
    # Example: "the cat 5000"
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            prev_word, next_word, freq = parts[0], parts[1], int(parts[2])
            
            # Store bigram count
            self.model[prev_word][next_word] += freq
            
            # Also insert next_word into trie for prefix completion
            self.trie.insert(next_word)
```

**Prediction Function:**
```python
def predict_next_word(self, prev_word: str, top_k: int = 5):
    # Get all words that follow prev_word
    if prev_word not in self.model:
        return []
    
    next_words = self.model[prev_word]  # Dict of {word → count}
    
    # Rank by frequency using Counter
    counter = Counter(next_words)
    return [w for w, _ in counter.most_common(top_k)]
```

**Example:**
```
User types: "good "
→ Look up self.model["good"]
→ Returns: {"morning": 8000, "afternoon": 3000, "night": 5000}
→ Ranked: ["morning", "night", "afternoon"]
```

#### Hybrid Prediction Strategy

Our `hybrid_predict` function combines multiple approaches:

```python
def hybrid_predict(self, user_input: str, top_k: int = 5):
    words = user_input.strip().split()
    
    # Case 1: Single word (incomplete) → Prefix completion
    if len(words) == 1:
        prefix = words[0]
        # Try bigram first (if "good" is a complete word)
        preds = self.predict_next_word(prefix, top_k)
        if preds:
            return preds
        # Fallback: prefix completion ("goo" → "good", "google")
        return self.predict_prefix(prefix, top_k)
    
    # Case 2: Multiple words → Bigram prediction
    if len(words) >= 2:
        prev_word = words[-2]  # Second-to-last word
        prefix = words[-1]      # Last word (might be incomplete)
        
        # Get bigram predictions based on prev_word
        next_candidates = self.predict_next_word(prev_word, top_k)
        
        # Get prefix completions for last word
        prefix_candidates = self.predict_prefix(prefix, top_k)
        
        # Combine: bigram predictions first, then prefix completions
        combined = list(dict.fromkeys(next_candidates + prefix_candidates))
        return combined[:top_k]
```

**Why This Strategy?**
1. **Bigrams capture context**: "good morning" is more common than "good banana"
2. **Prefix completion handles incomplete words**: "mor" → "morning"
3. **Fallback chain**: Bigram → Prefix → Spell check

---

### 3. Personalization System

#### How User Learning Works (`backend/personalization.py`)

**Data Structures:**
```python
class UserModel:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.personal_vocab = Counter()  # {word → count}
        self.personal_bigrams = defaultdict(lambda: defaultdict(int))
        self.recent_words = []  # Last 50 words typed
        self.total_interactions = 0
```

**Learning Process:**
```python
def learn(self, text: str):
    words = text.lower().split()
    
    # 1. Update vocabulary counts
    for word in words:
        self.personal_vocab[word] += 1  # Increment frequency
        
        # Track recent words (for recency bonus)
        if word in self.recent_words:
            self.recent_words.remove(word)
        self.recent_words.insert(0, word)
    
    # 2. Learn bigrams (word pairs)
    for i in range(len(words) - 1):
        self.personal_bigrams[words[i]][words[i+1]] += 1
    
    self.total_interactions += 1
```

**Example:**
```
User saves: "hello world"

After learning:
personal_vocab = {"hello": 1, "world": 1}
personal_bigrams = {"hello": {"world": 1}}

User saves "hello" again:
personal_vocab = {"hello": 2, "world": 1}
```

**Ranking with Personalization:**
```python
def get_personalized_suggestions(self, base_suggestions: list, boost_factor: float = 2.0):
    scored = []
    for word in base_suggestions:
        # Frequency score: How often user types this word
        frequency_score = self.personal_vocab.get(word, 0)
        
        # Recency score: Bonus if typed recently
        recency_score = 0
        if word in self.recent_words:
            position = self.recent_words.index(word)
            recency_score = (50 - position) / 50  # 0.0 to 1.0
        
        # Combined score (frequency weighted more)
        total_score = (frequency_score * boost_factor) + recency_score
        scored.append((word, total_score))
    
    # Sort: highest score first
    scored.sort(key=lambda x: -x[1])
    return [word for word, score in scored]
```

**Why This Scoring?**
- User-specific words rank higher (e.g., technical terms they use often)
- Recent words get small boost (user might be in a specific context)
- Still shows general suggestions if no personal match

**Persistence (JSON Storage):**
```python
def save_to_file(self, directory: str = 'user_data'):
    filepath = os.path.join(directory, f'{self.user_id}.json')
    
    data = {
        'user_id': self.user_id,
        'personal_vocab': dict(self.personal_vocab),
        'personal_bigrams': {k: dict(v) for k, v in self.personal_bigrams.items()},
        'recent_words': self.recent_words,
        'total_interactions': self.total_interactions
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

**Example JSON:**
```json
{
  "user_id": "student123",
  "personal_vocab": {
    "algorithm": 15,
    "data": 12,
    "structure": 10
  },
  "personal_bigrams": {
    "data": {"structure": 8, "analysis": 4}
  },
  "recent_words": ["algorithm", "sorting", "array"],
  "total_interactions": 42
}
```

---

## Backend Components Deep Dive

### Content Filter (`backend/content_filter.py`)

**Purpose:** Block inappropriate words from suggestions

**Implementation:**
```python
class ContentFilter:
    def __init__(self):
        self.blocked_words = set()
    
    def load_blocklist(self):
        # Load NSFW words from file
        with open('datasets/nsfw_words.txt', 'r') as f:
            for line in f:
                word = line.strip().lower()
                self.blocked_words.add(word)
    
    def filter_suggestions(self, suggestions: list) -> list:
        # Remove any blocked words
        return [s for s in suggestions if s.lower() not in self.blocked_words]
```

**Why Needed?**
- Dataset from internet may contain inappropriate words
- Ensures family-friendly suggestions
- Applied to ALL suggestions before returning to user

### Emoji Suggester (`backend/emoji_suggester.py`)

**Mapping Table:**
```python
self.emoji_map = {
    'happy': ['😊', '😄', '🎉', '😁'],
    'sad': ['😢', '😞', '💔'],
    'love': ['❤️', '💕', '😍'],
    'food': ['🍕', '🍔', '🍜'],
    # ... 100+ mappings
}
```

**Suggestion Logic:**
```python
def suggest(self, word: str, top_k: int = 3) -> list:
    word_lower = word.lower().strip()
    
    # Exact match
    if word_lower in self.emoji_map:
        return self.emoji_map[word_lower][:top_k]
    
    # Partial match (word contains key or key contains word)
    matches = []
    for key, emojis in self.emoji_map.items():
        if key in word_lower or word_lower in key:
            matches.extend(emojis)
    
    # Remove duplicates, return top-k
    return list(dict.fromkeys(matches))[:top_k]
```

**Example:**
```
Input: "happy" → Output: ['😊', '😄', '🎉']
Input: "birthday" → Output: ['🎂', '🎉', '🎁']
Input: "food" → Output: ['🍕', '🍔', '🍜']
```

### Language Detector (`backend/language_detector.py`)

**Unicode Range Detection:**
```python
LANGUAGE_RANGES = {
    'hindi': (0x0900, 0x097F),      # Devanagari script
    'tamil': (0x0B80, 0x0BFF),      # Tamil script
    'telugu': (0x0C00, 0x0C7F),     # Telugu script
    'malayalam': (0x0D00, 0x0D7F),  # Malayalam script
    'english': (0x0000, 0x007F)     # ASCII
}

def detect(self, text: str) -> str:
    counts = {lang: 0 for lang in LANGUAGE_RANGES}
    
    for char in text:
        code = ord(char)
        for lang, (start, end) in LANGUAGE_RANGES.items():
            if start <= code <= end:
                counts[lang] += 1
    
    # Return language with most characters
    return max(counts, key=counts.get)
```

**Why This Works?**
- Each Indian language uses distinct Unicode blocks
- Count characters in each range
- Highest count = detected language

---

## Frontend Implementation

### Key React Components (`frontend/src/pages/KeyboardPage.tsx`)

#### 1. Suggestions Fetching (Debounced)

```tsx
useEffect(() => {
  const fetchSuggestions = async () => {
    if (!input.trim()) {
      setSuggestions([]);
      return;
    }
    
    const words = input.trim().split(/\s+/);
    const lastWord = words[words.length - 1];
    const hasSpace = input.endsWith(' ');
    
    // Decide: autocomplete vs predict
    let apiUrl;
    if (hasSpace) {
      // User finished word, predict next
      apiUrl = `${API_BASE}/predict/${language}/?user_input=${input}`;
    } else {
      // User typing word, autocomplete
      apiUrl = `${API_BASE}/autocomplete/${language}/?prefix=${lastWord}`;
    }
    
    const response = await fetch(apiUrl);
    const data = await response.json();
    setSuggestions(data.suggestions || data.predictions);
  };
  
  // Debounce: wait 100ms after user stops typing
  const debounce = setTimeout(fetchSuggestions, 100);
  return () => clearTimeout(debounce);
}, [input, language]);
```

**Why Debouncing?**
- Prevents API spam (typing "hello" would make 5 requests without debounce)
- Waits for user to pause typing
- Improves performance and reduces server load

#### 2. Save to Dictionary

```tsx
const saveToPersonalization = async () => {
  // Extract last word
  const words = input.trim().split(/\s+/);
  const lastWord = words[words.length - 1];
  
  if (!lastWord || lastWord.length < 2) {
    setToast({ message: 'Word too short', type: 'error' });
    return;
  }
  
  // POST to /learn endpoint
  const response = await fetch(
    `${API_BASE}/learn/?user_id=${userId}&text=${lastWord}`,
    { method: 'POST' }
  );
  
  if (response.ok) {
    // Update UI with returned stats
    const data = await response.json();
    setDictionaryData(data.stats);
    setToast({ message: `Saved "${lastWord}"`, type: 'success' });
  }
};
```

**Flow:**
1. User types "algorithm"
2. Clicks "Save to Dictionary"
3. Frontend sends POST request
4. Backend calls `user_model.learn("algorithm")`
5. Backend saves JSON file immediately
6. Backend returns updated stats (word count, favorites)
7. Frontend updates dictionary display

#### 3. Emoji Suggestions (Per-Word)

```tsx
useEffect(() => {
  const fetchEmoji = async () => {
    if (enableEmojiSuggestions && input.trim().length > 0) {
      const words = input.trim().split(/\s+/);
      const lastWord = words[words.length - 1];
      
      if (lastWord.length > 1) {
        const response = await fetch(
          `${API_BASE}/emoji-suggest/?word=${lastWord}&top_k=3`
        );
        const data = await response.json();
        setEmojiSuggestions(data.emojis || []);
      }
    }
  };
  
  const debounce = setTimeout(fetchEmoji, 300);
  return () => clearTimeout(debounce);
}, [input, enableEmojiSuggestions]);
```

**Why Per-Word?**
- User sees emojis relevant to current word being typed
- Example: typing "happy" shows 😊😄🎉
- Updates as they continue typing next word

---

## How to Run & Test

### Backend Setup

```bash
cd backend

# Install dependencies
pip install fastapi uvicorn

# Start server
uvicorn main:app --reload

# Server runs on http://127.0.0.1:8000
```

### Testing Endpoints

**1. Test Autocomplete:**
```bash
curl "http://127.0.0.1:8000/autocomplete/english/?prefix=hel"
```
Expected: `{"suggestions": ["hello", "help", "held", ...]}`

**2. Test Prediction:**
```bash
curl "http://127.0.0.1:8000/predict/english/?user_input=good%20"
```
Expected: `{"predictions": ["morning", "afternoon", "night", ...]}`

**3. Test Personalization:**
```bash
# Save a word
curl -X POST "http://127.0.0.1:8000/learn/?user_id=test&text=algorithm"

# Check stats
curl "http://127.0.0.1:8000/user-stats/test"
```
Expected: `{"statistics": {"unique_words": 1, "total_words": 1, ...}}`

**4. Test Emoji:**
```bash
curl "http://127.0.0.1:8000/emoji-suggest/?word=happy&top_k=3"
```
Expected: `{"emojis": ["😊", "😄", "🎉"]}`

---

## Code Walkthrough

### Complete Flow: User Types "goo" → Sees "good", "google", "goose"

**Step 1: Frontend detects input change**
```tsx
// KeyboardPage.tsx
<textarea value={input} onChange={(e) => setInput(e.target.value)} />
```

**Step 2: Debounced effect triggers after 100ms**
```tsx
useEffect(() => {
  const fetchSuggestions = async () => {
    // input = "goo", hasSpace = false
    const apiUrl = `${API_BASE}/autocomplete/english/?prefix=goo`;
    const response = await fetch(apiUrl);
    setSuggestions(data.suggestions);
  };
  const debounce = setTimeout(fetchSuggestions, 100);
  return () => clearTimeout(debounce);
}, [input]);
```

**Step 3: Backend receives request**
```python
# main.py
@app.get("/autocomplete/{language}/")
async def autocomplete(language: str, prefix: str = Query(...)):
    suggestions = cached_autocomplete(prefix.lower(), language)
    # ... filtering and ranking ...
    return {"suggestions": suggestions[:10]}
```

**Step 4: Trie lookup**
```python
# trie.py
def autocomplete(prefix: str, max_suggestions: int = 10):
    # Step 4a: Find words starting with "goo"
    suggestions = starts_with(prefix, max_suggestions)
    # Result: ["good", "google", "goose", "goon", ...]
    
    # Step 4b: If no matches, try fuzzy search
    if not suggestions:
        suggestions = fuzzy_search(prefix, max_suggestions)
    
    # Step 4c: Final fallback: spell check
    if not suggestions:
        suggestions = spell_check(prefix, max_distance=2)
    
    return suggestions
```

**Step 5: Content filtering**
```python
# main.py (continued)
if filter_content:
    suggestions = content_filter.filter_suggestions(suggestions)
```

**Step 6: Personalization (if logged in)**
```python
if user_id:
    user_model = personalization_manager.get_user(user_id)
    suggestions = user_model.get_personalized_suggestions(suggestions)
    # If user frequently types "google", it ranks higher
```

**Step 7: Analytics boost**
```python
suggestions = word_analytics.boost_suggestions(suggestions)
# Common words get slight ranking boost
```

**Step 8: Return to frontend**
```python
return {"suggestions": ["good", "google", "goose"][:10]}
```

**Step 9: Frontend displays**
```tsx
{suggestions.map((suggestion, index) => (
  <button onClick={() => acceptSuggestion(suggestion)}>
    {suggestion.text}
  </button>
))}
```

**Step 10: User clicks "good"**
```tsx
const acceptSuggestion = (suggestion) => {
  const words = input.split(' ');
  words[words.length - 1] = suggestion.text;
  setInput(words.join(' ') + ' ');
  // Input becomes "good "
};
```

**Step 11: Prediction cycle starts**
- Input now ends with space → triggers prediction API
- Backend uses bigram model to predict next word after "good"
- Returns ["morning", "afternoon", "evening"]

---

### Complete Flow: User Saves "algorithm" to Dictionary

**Step 1: User clicks "Save to Dictionary"**
```tsx
<button onClick={saveToPersonalization}>
  Save to Dictionary
</button>
```

**Step 2: Frontend extracts last word**
```tsx
const saveToPersonalization = async () => {
  const words = input.trim().split(/\s+/);
  const lastWord = words[words.length - 1]; // "algorithm"
  
  const response = await fetch(
    `${API_BASE}/learn/?user_id=${userId}&text=${lastWord}`,
    { method: 'POST' }
  );
```

**Step 3: Backend receives POST request**
```python
# main.py
@app.post("/learn/")
async def learn_from_user(user_id: str, text: str):
    user_model = personalization_manager.get_user(user_id)
    # text = "algorithm"
```

**Step 4: Get or create user model**
```python
# personalization.py
def get_user(self, user_id: str) -> UserModel:
    if user_id in self.users:
        return self.users[user_id]
    
    # New user: create model
    user_model = UserModel(user_id)
    # Try to load existing data from JSON
    user_model.load_from_file(self.storage_dir)
    self.users[user_id] = user_model
    return user_model
```

**Step 5: Learn the word**
```python
# personalization.py
def learn(self, text: str):
    words = text.lower().split()  # ["algorithm"]
    
    for word in words:
        # Increment frequency counter
        self.personal_vocab[word] += 1
        # Before: {}
        # After: {"algorithm": 1}
        
        # Update recent words list
        if word in self.recent_words:
            self.recent_words.remove(word)
        self.recent_words.insert(0, word)
        # recent_words = ["algorithm", ...]
    
    self.total_interactions += 1
```

**Step 6: Save immediately to disk**
```python
# main.py (continued)
user_model.save_to_file()  # Write JSON immediately
```

**Step 7: Write JSON file**
```python
# personalization.py
def save_to_file(self, directory: str = 'user_data'):
    filepath = os.path.join(directory, f'{self.user_id}.json')
    
    data = {
        'user_id': self.user_id,
        'personal_vocab': {"algorithm": 1},
        'personal_bigrams': {},
        'recent_words': ["algorithm"],
        'total_interactions': 1
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    # File created: backend/user_data/student123.json
```

**Step 8: Return stats to frontend**
```python
# main.py (continued)
return {
    "status": "success",
    "user_id": user_id,
    "stats": {
        "unique_words": 1,
        "total_words": 1,
        "total_interactions": 1,
        "favorite_words": [["algorithm", 1]]
    }
}
```

**Step 9: Frontend updates UI**
```tsx
const response = await fetch(...);
if (response.ok) {
  const data = await response.json();
  setDictionaryData(data.stats);  // Update stats display
  setToast({ message: 'Saved "algorithm"', type: 'success' });
}
```

**Step 10: User sees confirmation**
- Toast message appears: "Saved 'algorithm' to your dictionary"
- Dictionary stats update (if modal is open)
- Next time user types "algo", "algorithm" ranks higher in suggestions

---

## Key Algorithms Summary

### 1. Trie Autocomplete
- **Time Complexity**: O(p + n) where p = prefix length, n = results
- **Space Complexity**: O(ALPHABET_SIZE × N × M) where N = words, M = avg length
- **Best for**: Prefix matching, fast lookups

### 2. Levenshtein Distance (Spell Check)
- **Time Complexity**: O(m × n) where m, n = word lengths
- **Space Complexity**: O(min(m, n)) with optimization
- **Best for**: Finding similar words, typo correction

### 3. N-gram (Bigram) Prediction
- **Time Complexity**: O(1) for lookup, O(k log k) for sorting top-k
- **Space Complexity**: O(V²) where V = vocabulary size
- **Best for**: Context-aware next-word prediction

### 4. Personalization Ranking
- **Time Complexity**: O(n log n) where n = suggestions
- **Space Complexity**: O(U) where U = user's unique words
- **Best for**: User-specific ranking, adaptive learning

---

## Performance Optimizations

### 1. LRU Caching
```python
@lru_cache(maxsize=1000)
def cached_autocomplete(prefix: str, language: str):
    return trie.autocomplete(prefix)
```
- Caches 1000 most recent queries
- Repeated queries return instantly
- Example: "he" → cached result reused for 1000 queries

### 2. Debouncing (Frontend)
- Waits 100ms after typing stops
- Prevents API spam (5 chars = 1 request, not 5)
- Reduces server load by 80%+

### 3. Early Termination
```python
while queue and len(suggestions) < 100:
    # Stop BFS once we have enough suggestions
```
- Don't explore entire trie if not needed
- Significantly faster for common prefixes

### 4. Frequency-Based Ranking
- Pre-sorted by frequency in dataset
- Most common words appear first
- No runtime sorting needed

---

## Testing & Validation

### Unit Tests You Can Write

**Test Trie Insert & Search:**
```python
def test_trie_basic():
    insert("hello", 1)
    insert("help", 1)
    insert("hero", 1)
    
    results = starts_with("hel", 10)
    assert "hello" in results
    assert "help" in results
    assert "hero" not in results  # doesn't start with "hel"
```

**Test Spell Check:**
```python
def test_spell_check():
    insert("cat", 1)
    insert("car", 1)
    insert("card", 1)
    
    corrections = spell_check("caz", max_distance=1)
    assert "cat" in corrections  # 1 edit: z→t
    assert "car" in corrections  # 1 edit: z→r
```

**Test Personalization:**
```python
def test_user_learning():
    user = UserModel("test")
    user.learn("hello")
    user.learn("hello")
    user.learn("world")
    
    assert user.personal_vocab["hello"] == 2
    assert user.personal_vocab["world"] == 1
    assert user.total_interactions == 3
```

---

## Conclusion

This system demonstrates several important CS concepts:

1. **Data Structures**: Trie, Hash Maps, Priority Queues
2. **Algorithms**: BFS, Dynamic Programming (Levenshtein), Sorting
3. **System Design**: REST API, Caching, Modular Architecture
4. **Machine Learning**: N-gram language models, Personalization

**Key Takeaways:**
- Trie enables O(p) prefix search vs O(n) linear scan
- N-grams capture language patterns from statistical data
- Personalization adapts system to individual users
- Modular design allows easy feature additions
- Performance optimizations make system responsive

---

## Appendix: File Structure

```
backend/
├── main.py                  # FastAPI app, API endpoints
├── trie.py                  # Trie implementation, autocomplete
├── n_gram.py               # Bigram model, prediction
├── personalization.py      # User learning, ranking
├── content_filter.py       # NSFW word filtering
├── emoji_suggester.py      # Emoji mapping
├── language_detector.py    # Unicode-based detection
├── analytics.py            # Word importance scoring
├── datasets/
│   ├── english.txt         # 387K English words
│   ├── 2_gram.txt          # Bigram frequencies
│   ├── hindi_dataset.txt   # Hindi words
│   ├── malayalam.txt       # Malayalam words
│   ├── tamil.txt           # Tamil words
│   ├── telugu.txt          # Telugu words
│   └── nsfw_words.txt      # Blocked words
└── user_data/              # User JSON files (created at runtime)
```
