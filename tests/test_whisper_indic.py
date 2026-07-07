#!/usr/bin/env python3
"""
Test script to verify Whisper STT improvements for Indic languages.
Tests the enhanced model with better decoding parameters and validation.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stt_service import transcribe_wav, _validate_indic_text, _get_decode_options

def test_validation():
    """Test the Indic text validation function."""
    print("\n=== Testing Indic Text Validation ===\n")
    
    test_cases = [
        # Valid Indic text
        ("नमस्ते मैं आपसे मिलकर खुश हूं", "hi", True, "Valid Hindi"),
        ("నమస్కారం నేను నిన్ను కలుసుకుని ఆనందిస్తున్నాను", "te", True, "Valid Telugu"),
        ("வணக்கம் நான் உங்களை சந்தித்து மகிழ்ச்சி அடைகிறேன்", "ta", True, "Valid Tamil"),
        
        # Invalid/garbled text
        ("asdfjkl; 12345 !!!", "hi", False, "Garbled/ASCII text for Hindi"),
        ("नमस्ते with some english", "hi", True, "Hindi with English (acceptable mixed)"),
        ("", "hi", False, "Empty text"),
        # Note: Pure ASCII for an Indic language will be rejected
        ("hello world", "hi", False, "Pure ASCII for Hindi"),
    ]
    
    for text, lang, expected, description in test_cases:
        result = _validate_indic_text(text, lang)
        status = "✓" if result == expected else "✗"
        print(f"{status} {description}")
        print(f"   Text: {text[:50]}... | Result: {result}")
        if result != expected:
            print(f"   ERROR: Expected {expected}, got {result}")
        print()

def test_decode_options():
    """Test the decode options for different languages."""
    print("\n=== Testing Decode Options ===\n")
    
    languages = ["en", "hi", "te", "ta"]
    
    for lang in languages:
        options = _get_decode_options(lang)
        print(f"Language: {lang}")
        print(f"  Beam size: {options.get('beam_size', 'N/A')}")
        print(f"  Temperature: {options.get('temperature')}")
        print(f"  No-speech threshold: {options.get('no_speech_threshold')}")
        print(f"  Logprob threshold: {options.get('logprob_threshold')}")
        print(f"  Has initial prompt: {'Yes' if options.get('initial_prompt') else 'No'}")
        print()

def test_model_loaded():
    """Verify the small model is loaded correctly."""
    print("\n=== Model Status ===\n")
    
    model_name = os.getenv("WHISPER_MODEL", "small")
    print(f"Configured model: {model_name}")
    print("Model loading is handled in stt_service.py on import.")
    print("If you see this without errors, the model loaded successfully!")

if __name__ == "__main__":
    print("=" * 60)
    print("Whisper STT Indic Language Improvement Tests")
    print("=" * 60)
    
    try:
        test_model_loaded()
        test_decode_options()
        test_validation()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Record some Hindi/Indic language audio samples")
        print("2. Test transcribe_wav() with the audio")
        print("3. Verify output is clean Indic script (no garbled characters)")
        print("4. Check confidence metrics logged to console")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
