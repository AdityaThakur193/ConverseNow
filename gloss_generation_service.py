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

    # 5. No match found
    return None


def generate_glosses(text: str) -> List[str]:
    """
    Convert English text to a sequence of ISL glosses.
    
    Args:
        text: English sentence/phrase
        
    Returns:
        List of ISL gloss words (animation names) that can be performed by the avatar.
        Returns empty list if input is empty or invalid.
        
    Example:
        >>> generate_glosses("Hello my name is Aditya")
        ['agree', 'he', 'he']  # "is" and "aditya" are skipped/unmapped
    """
    if not text or not text.strip():
        return []

    # Tokenize and clean
    words = _tokenize_and_clean(text)
    
    glosses = []
    for word in words:
        gloss = _get_gloss_for_word(word)
        
        # Only add if we found a match (gloss is not None)
        if gloss is not None and gloss in AVAILABLE_GLOSSES:
            glosses.append(gloss)
        else:
            # Log unknown words for debugging
            if gloss is None:
                print(f"Gloss generation: no mapping found for '{word}'")
    
    return glosses


def generate_glosses_with_confidence(text: str) -> dict:
    """
    Generate glosses with confidence metadata.
    
    Returns:
        {
            "glosses": ["hello", "my", "name", ...],
            "coverage": 0.85,  # Percentage of words successfully mapped
            "unmapped_words": ["aditya", ...],  # Words that couldn't be mapped
            "original_word_count": 5
        }
    """
    if not text or not text.strip():
        return {
            "glosses": [],
            "coverage": 0.0,
            "unmapped_words": [],
            "original_word_count": 0
        }

    words = _tokenize_and_clean(text)
    glosses = []
    unmapped_words = []

    for word in words:
        gloss = _get_gloss_for_word(word)
        
        if gloss and gloss in AVAILABLE_GLOSSES:
            glosses.append(gloss)
        else:
            unmapped_words.append(word)

    word_count = len(words)
    coverage = (word_count - len(unmapped_words)) / word_count if word_count > 0 else 0.0

    return {
        "glosses": glosses,
        "coverage": round(coverage, 2),
        "unmapped_words": unmapped_words,
        "original_word_count": word_count
    }


if __name__ == "__main__":
    # Test examples
    test_sentences = [
        "Hello my name is Aditya",
        "I like to work and play games",
        "Where is the hospital",
        "Please come home before monday",
        "Do you understand what I am saying",
    ]

    print("=" * 60)
    print("ISL Gloss Generation Service - Test Examples")
    print("=" * 60)

    for sentence in test_sentences:
        glosses = generate_glosses(sentence)
        confidence = generate_glosses_with_confidence(sentence)
        
        print(f"\nInput:  '{sentence}'")
        print(f"Glosses: {glosses}")
        print(f"Coverage: {confidence['coverage']*100:.0f}%")
        if confidence['unmapped_words']:
            print(f"Unmapped: {confidence['unmapped_words']}")
