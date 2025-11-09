from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
import trie
import n_gram
import os
from content_filter import content_filter
from language_detector import language_detector
from emoji_suggester import emoji_suggester
from analytics import word_analytics
from personalization import personalization_manager

app = FastAPI(title="Indic Autocomplete API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATASET_PATHS = {
    "english": "datasets/english.txt",
    "hindi": "datasets/hindi_dataset.txt",
    "malayalam": "datasets/malayalam.txt",
    "tamil": "datasets/tamil.txt",
    "telugu": "datasets/telugu.txt",
}

NGRAM_DATASET_PATHS = {
    "english": "datasets/2_gram.txt",
}

@app.on_event("startup")
async def startup_event():
    base_dir = os.path.dirname(__file__)
    for language, path in DATASET_PATHS.items():
        file_path = os.path.join(base_dir, path)
        if os.path.exists(file_path):
            trie.load_from_file(file_path)
    for language, path in NGRAM_DATASET_PATHS.items():
        file_path = os.path.join(base_dir, path)
        if os.path.exists(file_path):
            n_gram.load_from_file(file_path)
    # Phrase dataset deprecated; loading skipped.
    content_filter.load_blocklist()
    for language, path in DATASET_PATHS.items():
        file_path = os.path.join(base_dir, path)
        if os.path.exists(file_path):
            word_analytics.load_from_file(file_path)

@lru_cache(maxsize=1000)
def cached_autocomplete(prefix: str, language: str):
    return trie.autocomplete(prefix)

@lru_cache(maxsize=500)
def cached_predict(user_input: str, language: str):
    return n_gram.hybrid_predict(user_input)

@app.get("/")
async def root():
    return {"status": "running", "version": "2.0.0", "supported_languages": list(DATASET_PATHS.keys())}

@app.get("/autocomplete/{language}/")
async def autocomplete(language: str, prefix: str = Query(...), user_id: str = Query(None), filter_content: bool = Query(True)):
    suggestions = cached_autocomplete(prefix.lower(), language)
    if filter_content:
        suggestions = content_filter.filter_suggestions(suggestions)
    if user_id:
        user_model = personalization_manager.get_user(user_id)
        suggestions = user_model.get_personalized_suggestions(suggestions)
    suggestions = word_analytics.boost_suggestions(suggestions)
    return {"language": language, "prefix": prefix, "suggestions": suggestions[:10], "personalized": user_id is not None}

@app.get("/predict/{language}/")
async def predict(language: str, user_input: str = Query(...), user_id: str = Query(None), filter_content: bool = Query(True)):
    predictions = cached_predict(user_input.strip(), language)
    if filter_content:
        predictions = content_filter.filter_suggestions(predictions)
    if user_id:
        user_model = personalization_manager.get_user(user_id)
        words = user_input.strip().split()
        if words:
            personal_preds = user_model.predict_next_word(words[-1], top_k=5)
            if personal_preds:
                predictions = list(dict.fromkeys(personal_preds + predictions))
    return {"language": language, "context": user_input, "predictions": predictions[:10], "personalized": user_id is not None}

@app.get("/detect-language/")
async def detect_language(text: str = Query(...)):
    detected = language_detector.detect(text)
    confidence = language_detector.detect_with_confidence(text)
    is_multilingual = language_detector.is_multilingual(text)
    return {"text": text, "detected_language": detected, "confidence_scores": confidence, "is_multilingual": is_multilingual}

@app.get("/emoji-suggest/")
async def suggest_emoji(word: str = Query(...), top_k: int = Query(3)):
    emojis = emoji_suggester.suggest(word, top_k)
    return {"word": word, "emojis": emojis, "count": len(emojis)}

@app.post("/learn/")
async def learn_from_user(user_id: str = Query(...), text: str = Query(...)):
    user_model = personalization_manager.get_user(user_id)
    user_model.learn(text)
    
    # Only add custom words to Trie if they're likely real words (3+ chars and not similar to existing words)
    words = text.lower().split()
    for word in words:
        if len(word) >= 3:  # Only add words with 3+ characters to avoid typos
            if not trie.search(word):  # Only if not already in Trie
                # Check if word might be a typo by seeing if there are close matches
                suggestions = trie.spell_check(word, max_distance=1, max_results=1)
                if not suggestions:  # No close matches, likely a unique custom word
                    trie.insert(word, frequency=1)
                    print(f"Added custom word to Trie: {word}")
                else:
                    print(f"Skipped adding '{word}' - might be typo of '{suggestions[0]}'")
    
    # Persist immediately for project simplicity and predictable behavior
    user_model.save_to_file()
    return {"status": "success", "user_id": user_id, "stats": user_model.get_stats()}

@app.get("/user-stats/{user_id}")
async def get_user_stats(user_id: str):
    user_model = personalization_manager.get_user(user_id)
    stats = user_model.get_stats()
    return {"user_id": user_id, "statistics": stats}

@app.delete("/user-data/{user_id}")
async def delete_user_data(user_id: str):
    personalization_manager.delete_user(user_id)
    return {"status": "success", "message": f"Deleted all data for user {user_id}"}

@app.get("/spell-check/")
async def spell_check_word(word: str = Query(...), max_distance: int = Query(2), language: str = Query(None)):
    word_lower = word.lower()
    
    # First check if the word exists in the Trie (correctly spelled)
    word_exists = trie.search(word_lower)
    
    # Get spelling suggestions
    corrections = trie.spell_check(word_lower, max_distance=max_distance)
    
    # If word exists in dictionary, it's correct - don't show it as an error
    if word_exists:
        return {
            "word": word,
            "corrections": [],  # No corrections needed for correct words
            "found": True,
            "correct": True
        }
    
    # Word doesn't exist - return corrections
    return {
        "word": word,
        "corrections": corrections,
        "found": len(corrections) > 0,
        "correct": False
    }

@app.get("/word-analytics/")
async def get_word_importance(word: str = Query(...)):
    score = word_analytics.get_importance_score(word)
    tf = word_analytics.get_term_frequency(word)
    df = word_analytics.get_document_frequency(word)
    return {"word": word, "importance_score": round(score, 4), "term_frequency": tf, "document_frequency": df}

@app.get("/stats/")
async def get_system_stats():
    analytics_stats = word_analytics.get_stats()
    all_users = personalization_manager.get_all_user_ids()
    return {"system_status": "healthy", "word_analytics": analytics_stats, "content_filter": {"blocked_words_count": content_filter.get_blocklist_size()}, "personalization": {"total_users": len(all_users), "user_ids": all_users[:10]}, "supported_languages": list(DATASET_PATHS.keys())}
