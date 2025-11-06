# Indic Autocomplete Engine

A high-performance multilingual autocomplete and text prediction system supporting English, Hindi, Malayalam, Tamil, and Telugu languages.

## Features

- **Multilingual Support** - Native support for 5 languages with dedicated dictionaries
- **Smart Autocomplete** - Context-aware word completion using Trie-based search
- **Next Word Prediction** - N-gram based prediction for natural text flow
- **Personalization** - User-specific dictionary and learning from typing patterns
- **Spell Checking** - Real-time spell correction with edit distance algorithm
- **Content Filtering** - Built-in NSFW content blocking
- **Language Detection** - Automatic detection of input language
- **Emoji Suggestions** - Context-aware emoji recommendations
- **Virtual Keyboard** - On-screen keyboard for all supported languages

## Tech Stack

### Backend
- FastAPI 2.0.0
- Python 3.11+
- Custom Trie implementation
- N-gram language models
- LRU caching for performance

### Frontend
- React 18
- TypeScript
- Vite 7
- TailwindCSS
- Simple Keyboard component

## Installation

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### Start Frontend Server

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`

## API Endpoints

### Autocomplete
```
GET /autocomplete/{language}/?prefix={text}&user_id={id}&filter_content={bool}
```

### Prediction
```
GET /predict/{language}/?user_input={text}&user_id={id}&filter_content={bool}
```

### Spell Check
```
GET /spell-check/?word={word}&max_distance={int}
```

### Language Detection
```
GET /detect-language/?text={text}
```

### Emoji Suggestions
```
GET /emoji-suggest/?word={word}&top_k={int}
```

### Personalization
```
POST /learn/?user_id={id}&text={text}
GET /user-stats/{user_id}
DELETE /user-data/{user_id}
```

### Analytics
```
GET /word-analytics/?word={word}
GET /stats/
```

## Architecture

### Core Components

**Trie Data Structure**
- Efficient prefix-based word storage and retrieval
- Supports autocomplete with O(k) complexity where k is prefix length
- Spell checking using edit distance algorithm

**N-Gram Model**
- Predicts next word based on previous context
- Trained on language-specific datasets
 

**Personalization Engine**
- User-specific vocabulary tracking
- Frequency-based word ranking
- Bigram learning for contextual predictions
- Persistent storage in JSON format

**Content Filter**
- Dictionary-based word filtering
- Applied to all suggestions before display
- Always enabled for content safety

**Analytics System**
- TF-IDF based word importance scoring
- Document frequency tracking
- Suggestion ranking optimization

### Data Flow

```
User Input → Debounce (100ms) → API Request
                                      ↓
                        Backend Processing Pipeline:
                                      ↓
                        1. Trie Autocomplete / N-gram Prediction
                        2. Content Filter Application
                        3. Personalization (if user logged in)
                        4. Analytics Boost
                                      ↓
                        Top 3 Suggestions → Frontend Display
```

### File Structure

```
backend/
├── main.py                  # API endpoints and routing
├── trie.py                  # Autocomplete engine
├── n_gram.py               # Prediction engine
├── personalization.py      # User learning
├── content_filter.py       # Word filtering
├── language_detector.py    # Language detection
├── emoji_suggester.py      # Emoji mapping
├── analytics.py            # Word scoring
└── datasets/               # Language data files

frontend/
├── src/
│   ├── pages/KeyboardPage.tsx    # Main UI
│   ├── components/Toast.tsx      # Notifications
│   └── lib/layouts/              # Language keyboards
└── public/favicon.svg            # App icon
```

## Usage

1. Select a language from the top navigation
2. Start typing in the text area
3. View autocomplete suggestions below
4. Press Tab or click to accept suggestions
5. Enable optional features in Settings:
   - Language Detection
   - Emoji Suggestions
6. Login with a User ID to enable personalization
7. Save words to your personal dictionary
8. Check spelling with the spell check button

## Personalization

The system learns from your typing patterns and saves words to your personal dictionary. Each user maintains:

- Personal vocabulary with frequency counts
- Bigram patterns for next word prediction
- Interaction statistics

User data is stored locally in JSON files and persists across sessions.

## Performance

- Autocomplete: Sub-millisecond response time
- Prediction: Average 5ms response time
- LRU caching for frequently accessed suggestions
- Optimized Trie structure with 387,000+ words loaded
- Debounced API calls to minimize network requests

## Content Filtering

Content filtering is always enabled to maintain appropriate suggestions. The system filters inappropriate words from all results.

## License

MIT

## Author

Asterisk-Hunter
