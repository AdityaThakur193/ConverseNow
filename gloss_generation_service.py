"""
ISL (Indian Sign Language) Gloss Generation Service

Converts English text into a sequence of ISL glosses (sign words) that can be 
performed by the avatar. Uses a dictionary-based mapping with similarity fallback.
"""

import re
from typing import List, Optional
from difflib import SequenceMatcher

# Available ISL animations from Unity project (52 glosses + extra words)
AVAILABLE_GLOSSES = {
    "action", "agree", "almost", "ancient", "art", "available", "before", "body",
    "burden", "car", "careful", "clever", "come", "deafness", "die", "dizzy",
    "drive", "during", "education", "example", "experience", "expert", "explain",
    "finish", "follow", "game", "go", "government", "he", "hello", "home", "hospital",
    "idle", "independent", "interview", "january", "like", "monday", "must",
    "nature", "never", "operate", "other", "perfect", "please", "politician",
    "possible", "progress", "sunday", "tv", "where", "work",
    # Extra word animations from ISL_WE folder
    "bad", "best", "big", "call", "cold", "yes","you","what", "zero"
}

# English word → ISL gloss mapping dictionary
# Maps common English words to available ISL animations
GLOSS_DICTIONARY = {
    # Stop Words / Grammatical items to skip
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
    "s": None,
    "t": None,
    "d": None,
    "m": None,
    "ve": None,
    "ll": None,
    "re": None,

    # Exact mappings for available ISL animations to themselves
    "action": "action",
    "agree": "agree",
    "almost": "almost",
    "ancient": "ancient",
    "art": "art",
    "available": "available",
    "before": "before",
    "body": "body",
    "burden": "burden",
    "car": "car",
    "careful": "careful",
    "clever": "clever",
    "come": "come",
    "deafness": "deafness",
    "die": "die",
    "dizzy": "dizzy",
    "drive": "drive",
    "during": "during",
    "education": "education",
    "example": "example",
    "experience": "experience",
    "expert": "expert",
    "explain": "explain",
    "finish": "finish",
    "follow": "follow",
    "game": "game",
    "go": "go",
    "government": "government",
    "he": "he",
    "hello": "hello",
    "hi": "hello",
    "hey": "hello",
    "home": "home",
    "house": "home",
    "hospital": "hospital",
    "idle": "idle",
    "independent": "independent",
    "interview": "interview",
    "january": "january",
    "like": "like",
    "monday": "monday",
    "must": "must",
    "nature": "nature",
    "never": "never",
    "operate": "operate",
    "other": "other",
    "perfect": "perfect",
    "please": "please",
    "politician": "politician",
    "possible": "possible",
    "progress": "progress",
    "sunday": "sunday",
    "tv": "tv",
    "where": "where",
    "what": "what",
    "work": "work",
    "bad": "bad",
    "best": "best",
    "big": "big",
    "call": "call",
    "cold": "cold",
    "yes": "yes",
    "you": "you",
    "zero": "zero",
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
    "a": "A",
    "b": "B",
    "c": "C",
    "d": "D",
    "e": "E",
    "f": "F",
    "g": "G",
    "h": "H",
    "i": "I",
    "j": "J",
    "k": "K",
    "l": "L",
    "m": "M",
    "n": "N",
    "o": "O",
    "p": "P",
    "q": "Q",
    "r": "R",
    "s": "S",
    "t": "T",
    "u": "U",
    "v": "V",
    "w": "W",
    "x": "X",
    "y": "Y",
    "z": "Z",
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

    # 3. Substring match (for compound words) - skip short words/keys to avoid false matches (e.g. 'i')
    for key, gloss in GLOSS_DICTIONARY.items():
        if gloss is not None and len(key) >= 3 and len(word_lower) >= 3 and (key in word_lower or word_lower in key):
            return gloss

    # 4. Similarity match with HIGH threshold (0.75 minimum - very strict)
    similar_gloss = _find_similar_gloss(word_lower, threshold=0.75)
    if similar_gloss:
        return similar_gloss

    # 5. No match found - will use alphabet fallback
    return "ALPHABET_FALLBACK"


def generate_gloss_sequences(text: str) -> dict:
    """
    Generate the gloss sequence for avatar animation and a parallel display sequence 
    for UI text display. Spelled-out words map to the full uppercase word for each letter.
    """
    if not text or not text.strip():
        return {"glosses": [], "display": []}

    words = _tokenize_and_clean(text)
    glosses = []
    display = []

    for word in words:
        gloss = _get_gloss_for_word(word)
        
        # Check for stop word (None means skip)
        if gloss is None:
            continue
        
        # Check if the resolved gloss is available in Unity animations
        if gloss in AVAILABLE_GLOSSES:
            glosses.append(gloss)
            display.append(word.upper())
        else:
            # Fall back to fingerspelling (alphabet gloss)
            alphabet_gloss = _spell_word_with_alphabet(word)
            if alphabet_gloss:
                glosses.extend(alphabet_gloss)
                # Display the full word (in uppercase) prefixed with 'Fingerspelled-' for the duration of its spelled-out letters
                display.extend([f"Fingerspelled-{word.upper()}"] * len(alphabet_gloss))
                print(f"Gloss generation: spelling out '{word}' (animation '{gloss}' not available/missing)")
            else:
                print(f"Gloss generation: no mapping found for '{word}'")

    return {"glosses": glosses, "display": display}


def generate_glosses(text: str) -> List[str]:
    """
    Convert English text to a sequence of ISL glosses.
    
    Returns:
        List of ISL gloss words (animation names) that can be performed by the avatar.
    """
    return generate_gloss_sequences(text)["glosses"]


def generate_glosses_with_confidence(text: str) -> dict:
    """
    Generate glosses with confidence metadata.
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
    sequences = generate_gloss_sequences(text)
    glosses = sequences["glosses"]
    
    unmapped_words = []
    fallback_words = []
    
    # Identify which words were successfully mapped, fallback or unmapped
    for word in words:
        gloss = _get_gloss_for_word(word)
        if gloss is None:
            continue
        if gloss in AVAILABLE_GLOSSES:
            # Directly mapped
            pass
        else:
            alphabet_gloss = _spell_word_with_alphabet(word)
            if alphabet_gloss:
                fallback_words.append(word)
            else:
                unmapped_words.append(word)

    word_count = len(words)
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
