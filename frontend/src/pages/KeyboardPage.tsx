import { useMemo, useRef, useState, useEffect, useCallback } from 'react'
import Keyboard from 'react-simple-keyboard'
import 'simple-keyboard/build/css/index.css'
import type { KeyboardReactInterface } from 'react-simple-keyboard'
import { english } from '../lib/layouts/english'
import { hindi } from '../lib/layouts/hindi'
import { telugu } from '../lib/layouts/telugu'
import { malayalam } from '../lib/layouts/malayalam'
import { tamil } from '../lib/layouts/tamil'
import Toast from '../components/Toast'

const layouts = { english, hindi, telugu, malayalam, tamil };
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const REQUEST_TIMEOUT = 5000;

export default function KeyboardPage() {
  const [input, setInput] = useState<string>('')
  const [layoutName, setLayoutName] = useState<'default' | 'shift'>('default')
  const keyboardRef = useRef<KeyboardReactInterface | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const [language, setLanguage] = useState<keyof typeof layouts>('english');
  const [suggestions, setSuggestions] = useState<Array<{text: string; personalized: boolean}>>([]);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState<number>(0);
  const [userId, setUserId] = useState<string>(() => localStorage.getItem('autocomplete_user_id') || '');
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const filterContent = true;
  const [spellErrors, setSpellErrors] = useState<Array<{word: string; corrections: string[]}>>([]);
  const [isPersonalized, setIsPersonalized] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [toast, setToast] = useState<{message: string; type: 'success' | 'error'} | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [enableLanguageDetection, setEnableLanguageDetection] = useState<boolean>(false);
  const [enableEmojiSuggestions, setEnableEmojiSuggestions] = useState<boolean>(false);
  const [detectedLanguage, setDetectedLanguage] = useState<string>('');
  const [emojiSuggestions, setEmojiSuggestions] = useState<string[]>([]);
  const [showDictionary, setShowDictionary] = useState<boolean>(false);
  const [dictionaryData, setDictionaryData] = useState<{unique_words: number; total_words: number; favorite_words: Array<[string, number]>; total_interactions: number} | null>(null);

  useEffect(() => {
    if (userId) localStorage.setItem('autocomplete_user_id', userId);
    else localStorage.removeItem('autocomplete_user_id');
  }, [userId]);

  const handleLogin = useCallback(async () => {
    if (!userId.trim()) {
      setToast({ message: 'Please enter a User ID', type: 'error' });
      return;
    }

    setIsLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

      const response = await fetch(`${API_BASE}/user-stats/${encodeURIComponent(userId)}`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        setIsLoggedIn(true);
        
        const stats = data.statistics || {};
        const uniqueWords = stats.unique_words || 0;
        const totalWords = stats.total_words || 0;
        
        if (uniqueWords > 0) {
          setToast({ 
            message: `Loaded ${uniqueWords} unique words (${totalWords} total) from your dictionary`, 
            type: 'success' 
          });
        } else {
          setToast({ message: 'Logged in (new user - 0 words)', type: 'success' });
        }
      } else {
        setIsLoggedIn(true);
        setToast({ message: 'Logged in (new user - 0 words)', type: 'success' });
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        setToast({ message: 'Request timed out', type: 'error' });
      } else {
        setToast({ message: 'Failed to connect', type: 'error' });
      }
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!input.trim()) {
        setSuggestions([]);
        setIsPersonalized(false);
        return;
      }

      const words = input.trim().split(/\s+/);
      const lastWord = words[words.length - 1];
      const hasSpace = input.endsWith(' ');

      if (!hasSpace && lastWord.length < 2) {
        setSuggestions([]);
        return;
      }

      setIsLoading(true);
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

        const userParam = userId && isLoggedIn ? `&user_id=${encodeURIComponent(userId)}` : '';
        const filterParam = `&filter_content=${filterContent}`;
        
        let response;
        let apiUrl;
        if (hasSpace) {
          apiUrl = `${API_BASE}/predict/${language}/?user_input=${encodeURIComponent(input.trim())}${userParam}${filterParam}`;
          response = await fetch(apiUrl, { signal: controller.signal });
        } else {
          apiUrl = `${API_BASE}/autocomplete/${language}/?prefix=${encodeURIComponent(lastWord)}${userParam}${filterParam}`;
          response = await fetch(apiUrl, { signal: controller.signal });
        }
        
        clearTimeout(timeoutId);
        const data = await response.json();
        const rawResults = data.suggestions || data.predictions || [];
        
        const resultsWithMeta = rawResults.map((text: string) => ({
          text,
          personalized: data.personalized || false
        }));

  const personalizedSuggestions = resultsWithMeta.filter((s: {text: string; personalized: boolean}) => s.personalized);
  const otherSuggestions = resultsWithMeta.filter((s: {text: string; personalized: boolean}) => !s.personalized);
        
        const sortedResults = [...personalizedSuggestions, ...otherSuggestions].slice(0, 3);
        
        setSuggestions(sortedResults);
        setSelectedSuggestionIndex(0);
        setIsPersonalized(personalizedSuggestions.length > 0);
      } catch {
        setSuggestions([]);
        setIsPersonalized(false);
      } finally {
        setIsLoading(false);
      }
    };

    const debounce = setTimeout(fetchSuggestions, 100);
    return () => clearTimeout(debounce);
  }, [input, language, userId, isLoggedIn, filterContent]);

  useEffect(() => {
    const fetchLanguageAndEmoji = async () => {
      if (!input.trim()) {
        setDetectedLanguage('');
        setEmojiSuggestions([]);
        return;
      }

      try {
        if (enableLanguageDetection) {
          const response = await fetch(`${API_BASE}/detect-language/?text=${encodeURIComponent(input)}`);
          const data = await response.json();
          setDetectedLanguage(data.detected_language || '');
        } else {
          setDetectedLanguage('');
        }

        if (enableEmojiSuggestions && input.trim().length > 0) {
          const words = input.trim().split(/\s+/);
          const lastWord = words[words.length - 1];
          if (lastWord.length > 1) {
            const response = await fetch(`${API_BASE}/emoji-suggest/?word=${encodeURIComponent(lastWord)}&top_k=3`);
            const data = await response.json();
            setEmojiSuggestions((data.emojis || []).slice(0, 3));
          } else {
            setEmojiSuggestions([]);
          }
        } else {
          setEmojiSuggestions([]);
        }
      } catch {
        setEmojiSuggestions([]);
      }
    };

    const debounce = setTimeout(fetchLanguageAndEmoji, 300);
    return () => clearTimeout(debounce);
  }, [input, enableLanguageDetection, enableEmojiSuggestions]);

  const checkSpelling = useCallback(async () => {
    if (!input.trim()) {
      setSpellErrors([]);
      setToast({ message: 'Nothing to check', type: 'error' });
      return;
    }

    const words = input.split(/\s+/).filter(w => w.length > 0);
    const errors = [];

    setIsLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

      const results = await Promise.all(
        words.map(async (word) => {
          try {
            const response = await fetch(
              `${API_BASE}/spell-check/?word=${encodeURIComponent(word)}&language=${language}`,
              { signal: controller.signal }
            );
            const data = await response.json();
            return { word, corrections: data.corrections || [] };
          } catch {
            return { word, corrections: [] };
          }
        })
      );
      
      clearTimeout(timeoutId);
      errors.push(...results.filter(r => r.corrections.length > 0));
      setSpellErrors(errors);
      
      if (errors.length === 0) {
        setToast({ message: 'No spelling errors found', type: 'success' });
      } else {
        setToast({ message: `Found ${errors.length} spelling error${errors.length > 1 ? 's' : ''}`, type: 'error' });
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        setToast({ message: 'Spell check timed out', type: 'error' });
      } else {
        setToast({ message: 'Spell check failed', type: 'error' });
      }
    } finally {
      setIsLoading(false);
    }
  }, [input, language]);

  const saveToPersonalization = useCallback(async () => {
    if (!userId || !input.trim()) {
      setToast({ message: 'Please enter text to save', type: 'error' });
      return;
    }

    if (!isLoggedIn) {
      setToast({ message: 'Please login first', type: 'error' });
      return;
    }

    const words = input.trim().split(/\s+/).filter(word => word.length >= 2);
    
    if (words.length === 0) {
      setToast({ message: 'Please enter complete words (at least 2 characters)', type: 'error' });
      return;
    }

    setIsLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

      let successCount = 0;
      let failCount = 0;

      for (const word of words) {
        try {
          const response = await fetch(
            `${API_BASE}/learn/?user_id=${encodeURIComponent(userId)}&text=${encodeURIComponent(word)}`, 
            { method: 'POST', signal: controller.signal }
          );
          
          if (response.ok) {
            successCount++;
          } else {
            failCount++;
          }
        } catch {
          failCount++;
        }
      }
      
      clearTimeout(timeoutId);

      if (successCount > 0) {
        setToast({ 
          message: `Saved ${successCount} word${successCount > 1 ? 's' : ''} to your dictionary${failCount > 0 ? ` (${failCount} failed)` : ''}`, 
          type: successCount > failCount ? 'success' : 'error'
        });
      } else {
        setToast({ message: 'Failed to save words to dictionary', type: 'error' });
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        setToast({ message: 'Save timed out', type: 'error' });
      } else {
        setToast({ message: `Failed to save: ${error instanceof Error ? error.message : 'Unknown error'}`, type: 'error' });
      }
    } finally {
      setIsLoading(false);
    }
  }, [userId, input, isLoggedIn]);

  const viewDictionary = useCallback(async () => {
    if (!userId || !isLoggedIn) {
      setToast({ message: 'Please login first', type: 'error' });
      return;
    }

    setIsLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

      const response = await fetch(`${API_BASE}/user-stats/${encodeURIComponent(userId)}`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        const stats = data.statistics || {};
        setDictionaryData(stats);
        setShowDictionary(true);
      } else {
        setToast({ message: 'Failed to load dictionary', type: 'error' });
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        setToast({ message: 'Request timed out', type: 'error' });
      } else {
        setToast({ message: 'Failed to load dictionary', type: 'error' });
      }
    } finally {
      setIsLoading(false);
    }
  }, [userId, isLoggedIn]);

  const clearDictionary = useCallback(async () => {
    if (!userId || !isLoggedIn) {
      setToast({ message: 'Please login first', type: 'error' });
      return;
    }

    if (!confirm('Are you sure you want to clear your entire dictionary? This action cannot be undone.')) {
      return;
    }

    setIsLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

      const response = await fetch(`${API_BASE}/user-data/${encodeURIComponent(userId)}`, {
        method: 'DELETE',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (response.ok) {
        setToast({ message: 'Dictionary cleared successfully', type: 'success' });
        setShowDictionary(false);
        setDictionaryData(null);
      } else {
        setToast({ message: 'Failed to clear dictionary', type: 'error' });
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        setToast({ message: 'Request timed out', type: 'error' });
      } else {
        setToast({ message: 'Failed to clear dictionary', type: 'error' });
      }
    } finally {
      setIsLoading(false);
    }
  }, [userId, isLoggedIn]);

  const acceptSuggestion = useCallback((suggestion: {text: string; personalized: boolean}) => {
    const words = input.trim().split(/\s+/);
    const hasSpace = input.endsWith(' ');
    
    if (hasSpace) {
      const newInput = input + suggestion.text + ' ';
      setInput(newInput);
      keyboardRef.current?.setInput(newInput);
    } else {
      words[words.length - 1] = suggestion.text;
      const newInput = words.join(' ') + ' ';
      setInput(newInput);
      keyboardRef.current?.setInput(newInput);
    }
    
    setSuggestions([]);
    textareaRef.current?.focus();
  }, [input]);

  const applyCorrection = useCallback((original: string, correction: string) => {
    const newInput = input.replace(new RegExp(`\\b${original}\\b`, 'g'), correction);
    setInput(newInput);
    keyboardRef.current?.setInput(newInput);
    setSpellErrors(errors => errors.filter(e => e.word !== original));
    setToast({ message: `Corrected: ${original}  ${correction}`, type: 'success' });
  }, [input]);

  const keyboardOptions = useMemo(() => ({
    layoutName,
    layout: layouts[language],
    display: {
      '{bksp}': 'Backspace',
      '{enter}': 'Enter',
      '{tab}': 'Tab',
      '{lock}': 'Caps',
      '{shift}': 'Shift',
      '{space}': 'Space'
    },
    theme: 'hg-theme-default my-theme',
    buttonTheme: [
      { class: 'hg-highlight', buttons: '{enter} {bksp} {shift} {tab} {lock}' }
    ],
  onChange: (val: string) => setInput(val),
  onKeyPress: (button: string) => {
      if (button === '{shift}' || button === '{lock}') {
        setLayoutName((l) => (l === 'default' ? 'shift' : 'default'))
      }
      if (button === '{tab}' && suggestions.length > 0) {
        acceptSuggestion(suggestions[selectedSuggestionIndex]);
      }
    }
  }), [layoutName, language, suggestions, selectedSuggestionIndex, acceptSuggestion])

  return (
    <div className="w-full max-w-6xl mx-auto py-4 px-4">
      <div className="flex flex-col gap-4">
        
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {Object.keys(layouts).map((lang) => (
              <button
                key={lang}
                onClick={() => {
                  setLanguage(lang as keyof typeof layouts)
                  setLayoutName('default')
                }}
                className={`px-4 py-2 rounded border-2 border-white text-sm font-medium transition-all ${
                  language === lang 
                    ? 'bg-white text-black' 
                    : 'bg-black text-white hover:bg-white hover:text-black'
                }`}
              >
                {lang.charAt(0).toUpperCase() + lang.slice(1)}
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="px-3 py-2 rounded border-2 border-white bg-black text-white text-sm hover:bg-white hover:text-black transition-all"
          >
            Settings
          </button>
        </div>

        {showSettings && (
          <div className="p-4 rounded border-2 border-white bg-black space-y-3">
            <h3 className="text-lg font-bold">Settings</h3>
            
            <div>
              <label className="block text-sm font-medium mb-2">User ID (for personalization)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => {
                    setUserId(e.target.value);
                    setIsLoggedIn(false);
                  }}
                  placeholder="Enter your user ID..."
                  className="flex-1 px-3 py-2 rounded border-2 border-white bg-black text-white placeholder-gray-500 focus:outline-none focus:border-gray-400"
                />
                <button
                  onClick={handleLogin}
                  disabled={isLoading || !userId.trim()}
                  className={`px-4 py-2 rounded border-2 border-white text-sm font-medium transition-all ${
                    isLoggedIn 
                      ? 'bg-white text-black' 
                      : 'bg-black text-white hover:bg-white hover:text-black'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isLoading ? 'Loading...' : isLoggedIn ? 'Logged In' : 'Login'}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Language Detection</span>
              <button
                onClick={() => setEnableLanguageDetection(!enableLanguageDetection)}
                className={`px-4 py-1 rounded border-2 border-white text-sm transition-all ${
                  enableLanguageDetection ? 'bg-white text-black' : 'bg-black text-white'
                }`}
              >
                {enableLanguageDetection ? 'ON' : 'OFF'}
              </button>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Emoji Suggestions</span>
              <button
                onClick={() => setEnableEmojiSuggestions(!enableEmojiSuggestions)}
                className={`px-4 py-1 rounded border-2 border-white text-sm transition-all ${
                  enableEmojiSuggestions ? 'bg-white text-black' : 'bg-black text-white'
                }`}
              >
                {enableEmojiSuggestions ? 'ON' : 'OFF'}
              </button>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              keyboardRef.current?.setInput(e.target.value)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Tab' && suggestions.length > 0) {
                e.preventDefault();
                acceptSuggestion(suggestions[selectedSuggestionIndex]);
              }
            }}
            placeholder="Type here or use the keyboard below..."
            className="w-full h-32 border-2 border-white rounded p-3 text-lg bg-black text-white placeholder-gray-500 resize-none focus:outline-none focus:border-gray-400"
          />

          <div className="flex flex-wrap gap-2">
            <button
              onClick={checkSpelling}
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 rounded border-2 border-white bg-black text-white text-sm hover:bg-white hover:text-black disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Check Spelling
            </button>
            
            {userId && (
              <>
                <button
                  onClick={saveToPersonalization}
                  disabled={!input.trim() || isLoading || !isLoggedIn}
                  className="px-4 py-2 rounded border-2 border-white bg-black text-white text-sm hover:bg-white hover:text-black disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  Save to Dictionary
                </button>
                <button
                  onClick={viewDictionary}
                  disabled={isLoading || !isLoggedIn}
                  className="px-4 py-2 rounded border-2 border-white bg-black text-white text-sm hover:bg-white hover:text-black disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  View Dictionary
                </button>
              </>
            )}

            {isPersonalized && (
              <div className="px-3 py-2 rounded border-2 border-white bg-white text-black text-sm font-medium">
                Personalized
              </div>
            )}

            {detectedLanguage && (
              <div className="px-3 py-2 rounded border-2 border-white bg-white text-black text-sm font-medium">
                Detected: {detectedLanguage}
              </div>
            )}
          </div>
        </div>

        {emojiSuggestions.length > 0 && (
          <div className="flex flex-wrap gap-2 p-3 rounded border-2 border-white bg-black">
            <span className="text-sm text-gray-400">Emojis:</span>
            {emojiSuggestions.map((emoji, index) => (
              <button
                key={index}
                onClick={() => {
                  setInput(input + emoji);
                  keyboardRef.current?.setInput(input + emoji);
                }}
                className="px-3 py-1.5 rounded border-2 border-white bg-black text-white text-xl hover:bg-white hover:text-black transition-all"
              >
                {emoji}
              </button>
            ))}
          </div>
        )}

        {suggestions.length > 0 && (
          <div className="flex flex-wrap gap-2 p-3 rounded border-2 border-white bg-black">
            <span className="text-sm text-gray-400">Suggestions:</span>
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => acceptSuggestion(suggestion)}
                onMouseEnter={() => setSelectedSuggestionIndex(index)}
                className={`px-3 py-1.5 rounded border-2 text-sm font-medium transition-all ${
                  index === selectedSuggestionIndex
                    ? 'bg-white text-black border-white'
                    : suggestion.personalized
                    ? 'bg-gray-900 text-white border-gray-500 hover:border-white'
                    : 'bg-black text-white border-gray-600 hover:border-white'
                }`}
                title={suggestion.personalized ? 'From your dictionary' : 'General suggestion'}
              >
                {suggestion.text}
              </button>
            ))}
          </div>
        )}

        {spellErrors.length > 0 && (
          <div className="p-3 rounded border-2 border-white bg-black space-y-2">
            <div className="text-sm font-medium">Spelling Corrections:</div>
            {spellErrors.map((error, idx) => (
              <div key={idx} className="flex items-center gap-2 flex-wrap">
                <span className="text-red-400 font-medium">{error.word}</span>
                <span className="text-gray-400"></span>
                {error.corrections.slice(0, 3).map((correction, cidx) => (
                  <button
                    key={cidx}
                    onClick={() => applyCorrection(error.word, correction)}
                    className="px-2 py-1 rounded border border-white text-xs bg-black text-white hover:bg-white hover:text-black transition-all"
                  >
                    {correction}
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}

        <div className="rounded border-2 border-white p-2 bg-black">
          <Keyboard keyboardRef={(r) => (keyboardRef.current = r)} {...keyboardOptions} />
        </div>

        <style>{`
          .my-theme.hg-theme-default {
            background: #000000;
            border-radius: 0.5rem;
            font-family: system-ui, -apple-system, sans-serif;
          }
          .my-theme .hg-button {
            border-radius: 0.375rem;
            background: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
            height: 45px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.15s ease;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .my-theme .hg-button:hover {
            background: #ffffff;
            color: #000000;
          }
          .my-theme .hg-button:active {
            background: #ffffff;
            color: #000000;
            transform: scale(0.98);
          }
          .my-theme .hg-highlight {
            background: #1a1a1a;
            border-color: #888;
          }
        `}</style>
      </div>

      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}

      {showDictionary && dictionaryData && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-black border-2 border-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-white">Your Personal Dictionary</h2>
              <div className="flex gap-2">
                <button
                  onClick={clearDictionary}
                  disabled={isLoading}
                  className="px-4 py-2 rounded border-2 border-red-500 bg-black text-red-500 text-sm hover:bg-red-500 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  Clear Dictionary
                </button>
                <button
                  onClick={() => setShowDictionary(false)}
                  className="px-4 py-2 rounded border-2 border-white bg-black text-white text-sm hover:bg-white hover:text-black transition-all"
                >
                  Close
                </button>
              </div>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded border-2 border-white">
                  <p className="text-gray-400 text-sm">Unique Words</p>
                  <p className="text-2xl font-bold text-white">{dictionaryData.unique_words}</p>
                </div>
                <div className="p-4 rounded border-2 border-white">
                  <p className="text-gray-400 text-sm">Total Words</p>
                  <p className="text-2xl font-bold text-white">{dictionaryData.total_words}</p>
                </div>
                <div className="p-4 rounded border-2 border-white">
                  <p className="text-gray-400 text-sm">Total Interactions</p>
                  <p className="text-2xl font-bold text-white">{dictionaryData.total_interactions}</p>
                </div>
              </div>

              {dictionaryData.favorite_words && dictionaryData.favorite_words.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-xl font-bold text-white mb-3">Most Used Words</h3>
                  <div className="space-y-2">
                    {dictionaryData.favorite_words.map(([word, count], index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center p-3 rounded border-2 border-white bg-black hover:bg-white hover:text-black transition-all"
                      >
                        <span className="font-medium">{word}</span>
                        <span className="text-sm px-3 py-1 rounded border border-white">
                          {count} {count === 1 ? 'time' : 'times'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
