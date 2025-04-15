#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <map>
#include <algorithm>
#include <cctype>
#include <set>
#include <cmath>
#include "C:/Users/myalt/Libraries/eigen-3.4.0/Eigen/Dense"

using namespace std;
using namespace Eigen;

const double SUMMARY_RATIO = 0.5;
const double STOPWORD_PERCENTAGE = 0.015; // Top 1.5% of words as stopwords

string toLower(const string& str) {
    string result = str;
    transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

bool isPunctuation(char ch) {
    return ispunct(ch) && ch != '\'';
}

vector<string> splitIntoSentences(const string& text) {
    vector<string> sentences;
    stringstream ss(text);
    string segment, sentence;

    while (getline(ss, segment, '.')) {
        sentence = segment;
        if (!sentence.empty()) {
            sentence = toLower(sentence);
            sentence += ".";
            sentences.push_back(sentence);
        }
    }
    return sentences;
}

vector<string> tokenize(const string& sentence, const unordered_set<string>& stopwords) {
    vector<string> tokens;
    string word, cleaned;

    for (char ch : sentence) {
        cleaned += isPunctuation(ch) ? ' ' : tolower(ch);
    }

    stringstream ss(cleaned);
    while (ss >> word) {
        if (stopwords.find(word) == stopwords.end()) {
            tokens.push_back(word);
        }
    }
    return tokens;
}

vector<string> tokenizeAllWords(const string& text) {
    vector<string> words;
    string cleaned;
    for (char ch : text) {
        cleaned += isPunctuation(ch) ? ' ' : tolower(ch);
    }
    stringstream ss(cleaned);
    string word;
    while (ss >> word) {
        words.push_back(word);
    }
    return words;
}

unordered_set<string> generateStopwords(const string& text, const string& outputFile) {
    unordered_map<string, int> freq;
    auto words = tokenizeAllWords(text);

    for (const auto& word : words) {
        if (word.length() > 1) freq[word]++;
    }

    int topN = max(5, static_cast<int>(words.size() * STOPWORD_PERCENTAGE));
    vector<pair<string, int>> sorted(freq.begin(), freq.end());
    sort(sorted.begin(), sorted.end(), [](const auto& a, const auto& b) {
        return b.second < a.second;
    });

    unordered_set<string> stopwords;
    ofstream out(outputFile);
    for (int i = 0; i < min(topN, (int)sorted.size()); ++i) {
        stopwords.insert(sorted[i].first);
        out << sorted[i].first << "\n";
    }

    cout << "📝 Generated stopwords.txt with top " << stopwords.size() << " frequent words.\n";
    return stopwords;
}

void saveSummaryToFile(const vector<string>& summary, const string& filepath) {
    ofstream out(filepath);
    unordered_set<string> seen;
    for (const auto& sentence : summary) {
        if (seen.find(sentence) == seen.end()) {
            out << sentence << "\n";
            seen.insert(sentence);
        }
    }
}

void buildVocabulary(const vector<vector<string>>& tokenizedSentences,
                     unordered_map<string, int>& wordToIndex,
                     vector<unordered_map<string, int>>& sentenceTF) {
    set<string> vocabSet;
    for (const auto& tokens : tokenizedSentences) {
        unordered_map<string, int> tf;
        for (const auto& word : tokens) {
            tf[word]++;
            vocabSet.insert(word);
        }
        sentenceTF.push_back(tf);
    }

    int index = 0;
    for (const auto& word : vocabSet) {
        wordToIndex[word] = index++;
    }
}

MatrixXd computeTFIDF(const vector<unordered_map<string, int>>& sentenceTF,
                      const unordered_map<string, int>& wordToIndex,
                      int sentenceCount) {
    int vocabSize = wordToIndex.size();
    MatrixXd tfidf(vocabSize, sentenceCount);

    unordered_map<string, int> df;
    for (const auto& tf : sentenceTF) {
        for (const auto& term : tf) {
            df[term.first]++;
        }
    }

    for (int j = 0; j < sentenceCount; ++j) {
        const auto& tf = sentenceTF[j];
        for (const auto& term : tf) {
            int i = wordToIndex.at(term.first);
            double tfValue = static_cast<double>(term.second);
            double idf = log(static_cast<double>(sentenceCount) / (1 + df[term.first]));
            tfidf(i, j) = tfValue * idf;
        }
    }

    return tfidf;
}

vector<pair<int, double>> scoreSentences(const MatrixXd& tfidfMatrix) {
    JacobiSVD<MatrixXd> svd(tfidfMatrix, ComputeThinU | ComputeThinV);
    MatrixXd V = svd.matrixV();

    vector<pair<int, double>> scores;
    for (int i = 0; i < V.cols(); ++i) {
        double score = V.col(i).lpNorm<1>();
        scores.push_back({i, score});
    }

    sort(scores.begin(), scores.end(), [](const auto& a, const auto& b) {
        return b.second < a.second;
    });

    return scores;
}

int main() {
    string textFile = "input.txt";
    string stopwordFile = "stopwords.txt";

    ifstream file(textFile);
    if (!file.is_open()) {
        cerr << "❌ Failed to open input.txt\n";
        return 1;
    }

    stringstream buffer;
    buffer << file.rdbuf();
    string text = buffer.str();

    auto stopwords = generateStopwords(text, stopwordFile);
    auto sentences = splitIntoSentences(text);

    if (sentences.empty()) {
        cerr << "⚠️ No sentences found in input. Check for punctuation.\n";
        return 1;
    }

    vector<vector<string>> tokenizedSentences;
    for (const auto& sentence : sentences) {
        tokenizedSentences.push_back(tokenize(sentence, stopwords));
    }

    unordered_map<string, int> wordToIndex;
    vector<unordered_map<string, int>> sentenceTF;
    buildVocabulary(tokenizedSentences, wordToIndex, sentenceTF);
    MatrixXd tfidf = computeTFIDF(sentenceTF, wordToIndex, sentences.size());

    if (tfidf.cols() == 0 || tfidf.rows() == 0) {
        cerr << "⚠️ TF-IDF matrix is empty. Cannot compute summary.\n";
        return 1;
    }

    auto ranked = scoreSentences(tfidf);

    int summarySize = max(1, static_cast<int>(sentences.size() * SUMMARY_RATIO));
    set<int> selectedIndices;
    for (int i = 0; i < min(summarySize, (int)ranked.size()); ++i) {
        selectedIndices.insert(ranked[i].first);
    }

    vector<string> summary;
    for (int i = 0; i < sentences.size(); ++i) {
        if (selectedIndices.count(i)) {
            summary.push_back(sentences[i]);
        }
    }

    saveSummaryToFile(summary, "summary.txt");
    cout << "✅ Summary saved to summary.txt\n";
    return 0;
}
