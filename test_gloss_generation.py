#!/usr/bin/env python3
"""
Test suite for ISL Gloss Generation Service

Tests word mapping, gloss generation, and edge cases.
"""

from gloss_generation_service import (
    generate_glosses,
    generate_glosses_with_confidence,
    _get_gloss_for_word,
    _tokenize_and_clean,
    AVAILABLE_GLOSSES,
)


def test_word_mapping():
    """Test individual word mappings."""
    print("\n=== Testing Word Mapping ===\n")
    
    test_words = {
        "hello": "hello",
        "home": "home",
        "work": "work",
        "go": "go",
        "come": "come",
        "like": "like",
        "perfect": "perfect",
        "never": "never",
        "where": "where",
    }
    
    passed = 0
    failed = 0
    
    for word, expected_gloss in test_words.items():
        gloss = _get_gloss_for_word(word)
        status = "✓" if gloss == expected_gloss else "✗"
        print(f"{status} '{word}' → '{gloss}' (expected: '{expected_gloss}')")
        
        if gloss == expected_gloss:
            passed += 1
        else:
            failed += 1
    
    print(f"\nWord Mapping: {passed} passed, {failed} failed\n")
    return failed == 0


def test_tokenization():
    """Test text tokenization and cleaning."""
    print("\n=== Testing Tokenization ===\n")
    
    test_cases = {
        "Hello world!": ["hello", "world"],
        "What's your name?": ["what_is_your_name"],
        "I like to work and play!": ["i", "like", "to", "work", "and", "play"],
        "": [],
        "   ": [],
    }
    
    passed = 0
    failed = 0
    
    for text, expected_tokens in test_cases.items():
        tokens = _tokenize_and_clean(text)
        status = "✓" if tokens == expected_tokens else "✗"
        print(f"{status} '{text}' → {tokens}")
        
        if tokens == expected_tokens:
            passed += 1
        else:
            failed += 1
            print(f"   Expected: {expected_tokens}")
    
    print(f"\nTokenization: {passed} passed, {failed} failed\n")
    return failed == 0


def test_gloss_generation():
    """Test complete gloss generation."""
    print("\n=== Testing Gloss Generation ===\n")
    
    test_cases = [
        # Input → Expected glosses
        # Articles, prepositions, and proper names are correctly skipped/unmapped (or spelled out)
        ("Hello my name is Aditya", ["hello", "my_name_is", "A", "D", "I", "T", "Y", "A"]),  # "my name is" mapped to compound, aditya spelled out
        ("I like to work", ["I", "like", "work"]),  # "to" is skipped (preposition)
        ("Where is the home", ["where", "home"]),  # "is" and "the" skipped
        ("Come before finish", ["come", "before", "finish"]),
        ("Please do this carefully", ["please", "D", "O", "car"]),  # "this" has no good match, "do" spelled out, "carefully" -> "car" via substring
        ("", []),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_glosses in test_cases:
        glosses = generate_glosses(text)
        status = "✓" if glosses == expected_glosses else "✗"
        print(f"{status} '{text}'")
        print(f"   Got:      {glosses}")
        
        if glosses == expected_glosses:
            passed += 1
        else:
            failed += 1
            print(f"   Expected: {expected_glosses}")
        print()
    
    print(f"Gloss Generation: {passed} passed, {failed} failed\n")
    return failed == 0


def test_confidence_metrics():
    """Test gloss generation with confidence metadata."""
    print("\n=== Testing Confidence Metrics ===\n")
    
    test_cases = [
        ("hello world", 1.0),  # Both mapped (hello to dictionary, world spelled out)
        ("Hello my name is Aditya", 1.0),  # All mapped (hello, my, name to dictionary, is skipped, aditya spelled out)
        ("xyz abc def", 1.0),  # All spelled out via alphabet fallback
        ("", 0.0),  # Empty string
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_coverage in test_cases:
        result = generate_glosses_with_confidence(text)
        coverage = result["coverage"]
        status = "✓" if abs(coverage - expected_coverage) < 0.01 else "✗"
        print(f"{status} '{text}'")
        print(f"   Coverage: {coverage:.2f} (expected: {expected_coverage:.2f})")
        print(f"   Glosses: {result['glosses']}")
        if result['unmapped_words']:
            print(f"   Unmapped: {result['unmapped_words']}")
        
        if abs(coverage - expected_coverage) < 0.01:
            passed += 1
        else:
            failed += 1
        print()
    
    print(f"Confidence Metrics: {passed} passed, {failed} failed\n")
    return failed == 0


def test_gloss_validity():
    """Test that all generated glosses are valid (exist in AVAILABLE_GLOSSES or are letter fallbacks)."""
    print("\n=== Testing Gloss Validity ===\n")
    
    test_sentences = [
        "Hello my name is Aditya",
        "I like to work and play games",
        "Where is the hospital",
        "Please come home before monday",
        "Do you understand what I am saying",
    ]
    
    all_valid = True
    
    for sentence in test_sentences:
        glosses = generate_glosses(sentence)
        # Allow single-character fingerspelled letter fallbacks (A-Z)
        invalid = [g for g in glosses if g not in AVAILABLE_GLOSSES and not (len(g) == 1 and g.isalpha() and g.isupper())]
        
        if invalid:
            print(f"✗ '{sentence}'")
            print(f"   Invalid glosses: {invalid}")
            all_valid = False
        else:
            print(f"✓ '{sentence}'")
            print(f"   Glosses: {glosses}")
        print()
    
    return all_valid


def test_edge_cases():
    """Test edge cases and special inputs."""
    print("\n=== Testing Edge Cases ===\n")
    
    test_cases = [
        ("", []),
        ("   ", []),
        ("!!!", []),
        ("123 456", []),
        ("hello!!!", ["hello"]),
        ("...hello...", ["hello"]),
        ("HELLO WORLD", ["hello", "W", "O", "R", "L", "D"]),  # Case insensitivity & spelling fallback
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_glosses in test_cases:
        glosses = generate_glosses(text)
        status = "✓" if glosses == expected_glosses else "✗"
        print(f"{status} '{text}' → {glosses}")
        
        if glosses == expected_glosses:
            passed += 1
        else:
            failed += 1
            print(f"   Expected: {expected_glosses}")
    
    print(f"\nEdge Cases: {passed} passed, {failed} failed\n")
    return failed == 0


def main():
    """Run all tests."""
    print("=" * 60)
    print("ISL Gloss Generation Service - Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Word Mapping", test_word_mapping()))
    results.append(("Tokenization", test_tokenization()))
    results.append(("Gloss Generation", test_gloss_generation()))
    results.append(("Confidence Metrics", test_confidence_metrics()))
    results.append(("Gloss Validity", test_gloss_validity()))
    results.append(("Edge Cases", test_edge_cases()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed. Review output above.")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
