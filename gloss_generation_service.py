"""
ISL (Indian Sign Language) Gloss Generation Service

Converts English text into a sequence of ISL glosses (sign words) that can be 
performed by the avatar. Uses a dictionary-based mapping with similarity fallback.
"""

import re
from typing import List, Optional
from difflib import SequenceMatcher

# Available ISL animations from Unity project (50+ glosses)
AVAILABLE_GLOSSES = {
    "action", "agree", "almost", "ancient", "art", "available", "before", "body",
    "burden", "car", "careful", "clever", "come", "deafness", "die", "dizzy",
    "drive", "during", "education", "example", "experience", "expert", "explain",
    "finish", "follow", "game", "go", "government", "he", "home", "hospital",
    "idle", "independent", "interview", "january", "like", "monday", "must",
    "nature", "never", "operate", "other", "perfect", "please", "politician",
    "possible", "progress", "sunday", "tv", "where", "work"
}

# English word → ISL gloss mapping dictionary
# Maps common English words to available ISL animations
GLOSS_DICTIONARY = {
    # Greetings & Basics
    "hello": "agree",
    "hi": "agree",
    "hey": "agree",
    "bye": "follow",
    "goodbye": "follow",
    "yes": "agree",
    "ok": "agree",
    "okay": "agree",
    "no": "never",
    "not": "never",
    
    # Pronouns
    "i": "he",
    "me": "he",
    "my": "he",
    "you": "he",
    "your": "he",
    "he": "he",
    "she": "he",
    "it": "he",
    "we": "he",
    "our": "he",
    "they": "he",
    "their": "he",
    
    # Articles & Common Words to Skip (mapped to None internally)
    "a": None,
    "an": None,
    "the": None,
    "is": None,
    "are": None,
    "am": None,
    "be": None,
    "been": None,
    "being": None,
    "to": None,
    "of": None,
    "in": None,
    "at": None,
    "on": None,
    "by": None,
    "with": None,
    "from": None,
    "up": None,
    "about": None,
    "into": None,
    "through": None,
    "during": "during",  # "during" is a valid gloss
    "and": None,
    "or": None,
    "but": None,
    "as": None,
    "if": None,
    "because": None,
    "while": None,
    "until": None,
    "for": None,
    "this": None,
    "that": None,
    "these": None,
    "those": None,
    "which": None,
    "who": None,
    "whom": None,
    "whose": None,
    "s": None,  # From contractions like "what's"
    "t": None,  # From contractions
    "d": None,  # From contractions
    "m": None,  # From contractions
    "ve": None,  # From contractions
    "ll": None,  # From contractions
    "re": None,  # From contractions
    
    # Verbs - Movement & Action
    "go": "go",
    "come": "come",
    "walk": "go",
    "run": "go",
    "move": "go",
    "leave": "go",
    "arrive": "come",
    "approach": "come",
    "follow": "follow",
    "travel": "go",
    "drive": "drive",
    
    # Verbs - States & Actions
    "work": "work",
    "do": "action",
    "make": "action",
    "create": "action",
    "act": "action",
    "play": "game",
    "game": "game",
    "like": "like",
    "love": "like",
    "enjoy": "like",
    "agree": "agree",
    "disagree": "never",
    "understand": "perfect",
    "know": "perfect",
    
    # Verbs - Communication
    "say": "explain",
    "speak": "explain",
    "talk": "explain",
    "tell": "explain",
    "ask": "explain",
    "explain": "explain",
    "answer": "perfect",
    "listen": "follow",
    "hear": "follow",
    
    # Verbs - Duration
    "start": "action",
    "begin": "action",
    "finish": "finish",
    "end": "finish",
    "complete": "finish",
    "before": "before",
    "after": "finish",
    
    # Nouns - Places
    "home": "home",
    "house": "home",
    "hospital": "hospital",
    "school": "education",
    "office": "work",
    "government": "government",
    "place": "home",
    "location": "home",
    
    # Nouns - People & Roles
    "man": "he",
    "woman": "he",
    "person": "he",
    "people": "he",
    "politician": "politician",
    "expert": "expert",
    "teacher": "expert",
    "doctor": "expert",
    
    # Nouns - Things & Concepts
    "car": "car",
    "vehicle": "car",
    "thing": "action",
    "name": "he",
    "body": "body",
    "experience": "experience",
    "example": "example",
    "education": "education",
    "art": "art",
    "tv": "tv",
    "nature": "nature",
    "progress": "progress",
    
    # Nouns - Time
    "time": "during",
    "day": "during",
    "monday": "monday",
    "january": "january",
    "sunday": "sunday",
    "week": "during",
    "month": "january",
    "year": "january",
    
    # Adjectives & Qualities
    "good": "perfect",
    "great": "perfect",
    "perfect": "perfect",
    "bad": "burden",
    "terrible": "burden",
    "careful": "careful",
    "smart": "clever",
    "clever": "clever",
    "independent": "independent",
    "dizzy": "dizzy",
    "sick": "dizzy",
    "tired": "idle",
    "lazy": "idle",
    "possible": "possible",
    "impossible": "never",
    "available": "available",
    
    # Adjectives - States/Emotions
    "alive": "action",
    "dead": "die",
    "ancient": "ancient",
    "old": "ancient",
    "new": "available",
    "happy": "like",
    "sad": "burden",
    "angry": "burden",
    
    # Adverbs & Modifiers
    "almost": "almost",
    "never": "never",
    "always": "action",
    "please": "please",
    "must": "must",
    "should": "must",
    "can": "perfect",
    "will": "action",
    "would": "action",
    
    # Miscellaneous
    "what": "explain",
    "where": "where",
    "when": "during",
    "why": "explain",
    "how": "explain",
    "other": "other",
    "operate": "operate",
    "interview": "interview",
    "deafness": "deafness",
    "deaf": "deafness",
}

# Part-of-Speech based fallback mapping (when similarity match fails)
POS_FALLBACK = {
    "NOUN": "action",
    "VERB": "action",
    "ADJ": "perfect",
    "ADV": "action",
    "PRON": "he",
}

# Alphabet gloss mapping for letter-by-letter spelling fallback
# When a word is not found in the dictionary, it falls back to spelling it out
ALPHABET_GLOSS = {
    "a": "a_sign",
    "b": "b_sign",
    "c": "c_sign",
    "d": "d_sign",
    "e": "e_sign",
    "f": "f_sign",
    "g": "g_sign",
    "h": "h_sign",
    "i": "i_sign",
    "j": "j_sign",
    "k": "k_sign",
    "l": "l_sign",
    "m": "m_sign",
    "n": "n_sign",
    "o": "o_sign",
    "p": "p_sign",
    "q": "q_sign",
    "r": "r_sign",
    "s": "s_sign",
    "t": "t_sign",
    "u": "u_sign",
    "v": "v_sign",
    "w": "w_sign",
    "x": "x_sign",
    "y": "y_sign",
    "z": "z_sign",
}


def _similarity_score(word1: str, word2: str) -> float:
    """Calculate similarity between two words (0-1 scale)."""
    return SequenceMatcher(None, word1.lower(), word2.lower()).ratio()


def _find_similar_gloss(word: str, threshold: float = 0.6) -> Optional[str]:
    """
    Find a similar gloss using string similarity matching.
    
    Returns the best matching gloss if similarity >= threshold.
    """
    best_match = None
    best_score = threshold

    for gloss in AVAILABLE_GLOSSES:
        score = _similarity_score(word, gloss)
        if score > best_score:
            best_score = score
            best_match = gloss

    return best_match


def _spell_word_with_alphabet(word: str) -> List[str]:
    """
    Spell out a word letter-by-letter using alphabet gloss.
    
    Used as fallback when a word is not found in the gloss dictionary.
    Returns a list of alphabet glosses for each letter in the word.
    
    Args:
        word: Word to spell out
        
    Returns:
        List of alphabet glosses (e.g., ['a_sign', 'b_sign', 'c_sign'])
        Empty list if word contains characters not in alphabet
    """
    alphabet_gloss = []
    word_lower = word.lower().strip()
    
    for char in word_lower:
        if char in ALPHABET_GLOSS:
            alphabet_gloss.append(ALPHABET_GLOSS[char])
        elif char.isalpha():
            # Character exists but not in our alphabet mapping
            # Skip it or handle gracefully
            continue
    
    return alphabet_gloss


def _tokenize_and_clean(text: str) -> List[str]:
    """
    Tokenize text into words and clean them.
    Removes punctuation and converts to lowercase.
    """
    if not text or not text.strip():
        return []

    # Remove punctuation but keep spaces
    text = re.sub(r"[^\w\s]", " ", text)
    
    # Split on whitespace
    words = text.split()
    
    # Convert to lowercase and filter empty strings
    return [word.lower() for word in words if word.strip()]


def _get_gloss_for_word(word: str) -> Optional[str]:
    """
    Get the ISL gloss for a given English word.
    
    Strategy:
    1. Check if it's a stop word (articles, prepositions, etc.) - return None
    2. Exact match in dictionary
    3. Substring match in dictionary (e.g., "goodbye" contains "bye")
    4. Similarity match (high threshold - 0.75+)
    5. Return None if no reasonable match found
    """
    if not word:
        return None

    word_lower = word.lower().strip()

    # 1. Check for stop words / words to skip (mapped to None)
    if word_lower in GLOSS_DICTIONARY:
        gloss = GLOSS_DICTIONARY[word_lower]
        if gloss is None:
            return None  # Skip this word
        return gloss

    # 2. Exact match (already checked above, but keeping for clarity)
    if word_lower in GLOSS_DICTIONARY:
        gloss = GLOSS_DICTIONARY[word_lower]
        if gloss is not None:
            return gloss

    # 3. Substring match (for compound words)
    for key, gloss in GLOSS_DICTIONARY.items():
        if gloss is not None and key and (key in word_lower or word_lower in key):
            return gloss

    # 4. Similarity match with HIGH threshold (0.75 minimum - very strict)
    similar_gloss = _find_similar_gloss(word_lower, threshold=0.75)
    if similar_gloss:
        return similar_gloss

    # 5. No match found - will use alphabet fallback
    return "ALPHABET_FALLBACK"


def generate_glosses(text: str) -> List[str]:
    """
    Convert English text to a sequence of ISL glosses.
    
    Strategy:
    1. Try to find gloss in dictionary or through similarity matching
    2. If word not found, spell it out letter-by-letter using alphabet gloss (fallback)
    3. Skip stop words (articles, prepositions, etc.)
    
    Args:
        text: English sentence/phrase
        
    Returns:
        List of ISL gloss words (animation names) that can be performed by the avatar.
        For unmapped words, returns individual letter glosses (e.g., 'aditya' → ['a_sign', 'd_sign', 'i_sign', 't_sign', 'y_sign', 'a_sign'])
        Returns empty list if input is empty or invalid.
        
    Example:
        >>> generate_glosses("Hello my name is Aditya")
        ['agree', 'he', 'he', 'a_sign', 'd_sign', 'i_sign', 't_sign', 'y_sign', 'a_sign']
    """
    if not text or not text.strip():
        return []

    # Tokenize and clean
    words = _tokenize_and_clean(text)
    
    glosses = []
    for word in words:
        gloss = _get_gloss_for_word(word)
        
        # Check for stop word (None means skip)
        if gloss is None:
            continue
        
        # Check if word is in dictionary or found through similarity matching
        if gloss in AVAILABLE_GLOSSES:
            glosses.append(gloss)
        # Check if we need alphabet fallback
        elif gloss == "ALPHABET_FALLBACK":
            alphabet_gloss = _spell_word_with_alphabet(word)
            if alphabet_gloss:
                glosses.extend(alphabet_gloss)
                print(f"Gloss generation: spelling out '{word}' using alphabet gloss")
            else:
                print(f"Gloss generation: no mapping found for '{word}'")
    
    return glosses


def generate_glosses_with_confidence(text: str) -> dict:
    """
    Generate glosses with confidence metadata.
    
    Returns:
        {
            "glosses": ["hello", "my", "name", ...],
            "coverage": 0.85,  # Percentage of words successfully mapped
            "unmapped_words": ["words_that_had_no_alphabet_match", ...],  # Words that couldn't be mapped even with alphabet
            "fallback_words": ["aditya", ...],  # Words that used alphabet gloss fallback
            "original_word_count": 5
        }
    """
    if not text or not text.strip():
        return {
            "glosses": [],
            "coverage": 0.0,
            "unmapped_words": [],
            "fallback_words": [],
            "original_word_count": 0
        }

    words = _tokenize_and_clean(text)
    glosses = []
    unmapped_words = []
    fallback_words = []

    for word in words:
        gloss = _get_gloss_for_word(word)
        
        # Skip stop words
        if gloss is None:
            continue
        
        # Word found in dictionary
        if gloss in AVAILABLE_GLOSSES:
            glosses.append(gloss)
        # Use alphabet fallback
        elif gloss == "ALPHABET_FALLBACK":
            alphabet_gloss = _spell_word_with_alphabet(word)
            if alphabet_gloss:
                glosses.extend(alphabet_gloss)
                fallback_words.append(word)
            else:
                # Couldn't generate alphabet gloss (no valid letters)
                unmapped_words.append(word)

    word_count = len(words)
    # Coverage: words that were either dictionary-mapped or alphabet-fallback
    mapped_count = word_count - len(unmapped_words)
    coverage = mapped_count / word_count if word_count > 0 else 0.0

    return {
        "glosses": glosses,
        "coverage": round(coverage, 2),
        "unmapped_words": unmapped_words,
        "fallback_words": fallback_words,
        "original_word_count": word_count
    }


if __name__ == "__main__":
    # Test examples - including complex sentences
    test_sentences = [
        # Basic tests
        "Hello my name is Aditya",
        "I like to work and play games",
        "Where is the hospital",
        "Please come home before monday",
        "Do you understand what I am saying",
        
        # Complex sentences with unmapped words
        "My favorite color is blue",
        "I speak xyz language",
        
        # Complex real-world sentences
        "Could you please help me understand this complex problem",
        "The doctor explained the diagnosis to my family yesterday",
        "I want to travel to Japan and visit Tokyo next summer",
        "What is your preferred method of communication",
        "Mathematics and science are fascinating subjects to explore",
        "The weather was beautiful throughout the entire weekend",
        "I cannot believe how quickly everything happened today",
        "Can you recommend some good restaurants in the downtown area",
    ]

    print("=" * 70)
    print("ISL Gloss Generation Service - Comprehensive Test Suite")
    print("=" * 70)

    total_words = 0
    total_glosses = 0
    total_fallback = 0

    for sentence in test_sentences:
        glosses = generate_glosses(sentence)
        confidence = generate_glosses_with_confidence(sentence)
        
        print(f"\n{'─' * 70}")
        print(f"Input:  '{sentence}'")
        print(f"Glosses: {glosses}")
        print(f"Total Glosses Generated: {len(glosses)}")
        print(f"Coverage: {confidence['coverage']*100:.0f}%")
        
        if confidence['fallback_words']:
            print(f"Alphabet Fallback Used For: {confidence['fallback_words']} ({len(confidence['fallback_words'])} words)")
        if confidence['unmapped_words']:
            print(f"Unmapped: {confidence['unmapped_words']}")
        
        total_words += confidence['original_word_count']
        total_glosses += len(glosses)
        total_fallback += len(confidence['fallback_words'])

    print(f"\n{'═' * 70}")
    print("SUMMARY STATISTICS")
    print(f"{'═' * 70}")
    print(f"Total Test Sentences: {len(test_sentences)}")
    print(f"Total Words Processed: {total_words}")
    print(f"Total Glosses Generated: {total_glosses}")
    print(f"Words Using Alphabet Fallback: {total_fallback}")
    print(f"Overall Gloss Generation: {total_glosses}/{total_words} = {(total_glosses/total_words)*100:.1f}%")
