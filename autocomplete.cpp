#include <bits/stdc++.h>
#include "Trie.cpp"
using namespace std;

class AutoComplete {
public:
    static vector<string> wordsWithPrefix(Trie& trie, const string& prefix, int maxSuggestions = INT_MAX) {
        vector<string> suggestions;

        Trie::Node* node = trie.root;
        for (char c : prefix) {
            node = node->get(c);
            if (!node) return suggestions;
        }

        dfs(node, prefix, maxSuggestions, suggestions);
        return suggestions;
    }

private:
    static void dfs(Trie::Node* node, const string& currentWord, int maxCount, vector<string>& suggestions) {
        if ((int)suggestions.size() >= maxCount) return;

        if (node->isEnd()) {
            suggestions.push_back(currentWord);
            if ((int)suggestions.size() >= maxCount) return;
        }

        for (char c = 'a'; c <= 'z'; c++) {
            if ((int)suggestions.size() >= maxCount) return;
            if (node->containsKey(c)) {
                dfs(node->get(c), currentWord + c, maxCount, suggestions);
            }
        }
    }
};

int main() {
    Trie trie;

    ifstream dictFile("New_words.txt"); 
    if (!dictFile.is_open()) {
        cerr << "Error: Could not open New_words.txt\n";
        return 1;
    }

    string line;
    unordered_set<string> seen; 
    while (getline(dictFile, line)) {
        stringstream ss(line);
        string word;
        while (ss >> word) { 
            for (char& c : word) c = tolower(c);

            string cleanWord;
            for (char c : word) {
                if (c >= 'a' && c <= 'z') cleanWord.push_back(c);
            }

            if (!cleanWord.empty() && !seen.count(cleanWord)) {
                trie.insert(cleanWord);
                seen.insert(cleanWord);
            }
        }
    }
    dictFile.close();

    string prefix;
    cout << "Enter prefix: ";
    cin >> prefix;

    for (char& c : prefix) c = tolower(c);

    vector<string> suggestions = AutoComplete::wordsWithPrefix(trie, prefix, 5);

    cout << "Autocomplete suggestions for '" << prefix << "':\n";
    for (const string& suggestion : suggestions) {
        cout << suggestion << "\n";
    }

    return 0;
}
