"""
Roman to Devanagari Transliteration - AKSHARAMUKHA VERSION
==========================================================
Production-ready module using Aksharamukha library.
Includes comprehensive testing and debugging.

Installation:
    pip install aksharamukha

Author: Voter Search System
Date: 2026-01-31
"""

import re
import streamlit as st
from typing import Optional

# ============================================================================
# AKSHARAMUKHA IMPORT WITH DEBUG INFO
# ============================================================================

AKSHARAMUKHA_AVAILABLE = False
IMPORT_ERROR = None

try:
    from aksharamukha import transliterate
    AKSHARAMUKHA_AVAILABLE = True
    print("✅ Aksharamukha loaded successfully!")
except ImportError as e:
    IMPORT_ERROR = str(e)
    print(f"❌ Aksharamukha not available: {e}")
    print("   Install with: pip install aksharamukha")


def is_devanagari(text: str) -> bool:
    """
    Check if the input text is already in Devanagari script.
    
    Args:
        text: Input string to check
        
    Returns:
        True if text contains Devanagari characters, False otherwise
    """
    if not text:
        return False
    
    # Devanagari Unicode range: U+0900 to U+097F
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    return bool(devanagari_pattern.search(text))


def is_roman(text: str) -> bool:
    """
    Check if the input text is in Roman script (English alphabet).
    
    Args:
        text: Input string to check
        
    Returns:
        True if text contains only Roman characters, False otherwise
    """
    if not text:
        return False
    
    # Check if text contains only ASCII letters, numbers, and common punctuation
    roman_pattern = re.compile(r'^[a-zA-Z0-9\s\-.,/]+$')
    return bool(roman_pattern.match(text))


@st.cache_data(show_spinner=False)
def roman_to_devanagari_aksharamukha(text: str) -> str:
    """
    Convert Roman script to Devanagari using Aksharamukha.
    
    This function uses the industry-standard Aksharamukha library
    for accurate transliteration.
    
    Args:
        text: Input text in Roman script
        
    Returns:
        Transliterated text in Devanagari script
        
    Examples:
        >>> roman_to_devanagari_aksharamukha("ram")
        'राम'
        >>> roman_to_devanagari_aksharamukha("nepal")
        'नेपाल'
    """
    if not text or not text.strip():
        return text
    
    if not AKSHARAMUKHA_AVAILABLE:
        print(f"⚠️ Aksharamukha not available, returning original: {text}")
        return text
    
    try:
        # Convert using Aksharamukha
        # ISO scheme works well for standard Roman transliteration
        devanagari_text = transliterate.process(
            'ISO',           # Source: ISO/IAST transliteration
            'Devanagari',    # Target: Devanagari script
            text,
            pre_options=['IgnoreVedicAccents'],
            post_options=['IgnoreSwaras']
        )
        
        print(f"🔄 Converted: '{text}' → '{devanagari_text}'")
        return devanagari_text
        
    except Exception as e:
        print(f"❌ Conversion error for '{text}': {e}")
        return text


def smart_convert_to_devanagari(text: str) -> str:
    """
    Intelligently convert input to Devanagari.
    
    This function:
    1. Detects if input is already Devanagari (returns as-is)
    2. Detects if input is Roman (converts to Devanagari)
    3. Logs all conversions for debugging
    
    Args:
        text: User input in any script
        
    Returns:
        Text in Devanagari script (or original if already Devanagari)
        
    Examples:
        >>> smart_convert_to_devanagari("ram")
        'राम'
        >>> smart_convert_to_devanagari("राम")
        'राम'
    """
    if not text or not text.strip():
        return text
    
    text = text.strip()
    
    # Check if already Devanagari
    if is_devanagari(text):
        print(f"✅ Already Devanagari: '{text}'")
        return text
    
    # Check if Roman
    if is_roman(text):
        print(f"🔄 Converting Roman: '{text}'")
        converted = roman_to_devanagari_aksharamukha(text)
        print(f"   Result: '{converted}'")
        return converted
    
    # Unknown format
    print(f"⚠️ Unknown format, attempting conversion: '{text}'")
    return roman_to_devanagari_aksharamukha(text)


def check_installation():
    """
    Check if Aksharamukha is properly installed.
    Returns status and instructions.
    """
    if AKSHARAMUKHA_AVAILABLE:
        return {
            'installed': True,
            'message': '✅ Aksharamukha is installed and working!',
            'version': 'Available'
        }
    else:
        return {
            'installed': False,
            'message': '❌ Aksharamukha is NOT installed',
            'error': IMPORT_ERROR,
            'instructions': '''
To install Aksharamukha:

1. Using pip:
   pip install aksharamukha

2. Using pip with system packages flag:
   pip install aksharamukha --break-system-packages

3. In a virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install aksharamukha

4. For Streamlit Cloud, add to requirements.txt:
   aksharamukha>=1.0.0
'''
        }


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_transliteration():
    """Test transliteration with common Nepali words and names."""
    
    print("\n" + "=" * 70)
    print("AKSHARAMUKHA INSTALLATION CHECK")
    print("=" * 70)
    
    status = check_installation()
    print(status['message'])
    if not status['installed']:
        print(f"\nError: {status['error']}")
        print(status['instructions'])
        return
    
    print("\n" + "=" * 70)
    print("TRANSLITERATION TEST RESULTS")
    print("=" * 70)
    
    test_cases = [
        # Common names
        ("ram", "राम"),
        ("sita", "सीता"),
        ("hari", "हरि"),
        ("krishna", "कृष्ण"),
        
        # Places
        ("nepal", "नेपाल"),
        ("kathmandu", "काठमाडौं"),
        ("pokhara", "पोखरा"),
        
        # Common words
        ("namaste", "नमस्ते"),
        ("dhanyabad", "धन्यबाद"),
        ("maya", "माया"),
        ("devi", "देवी"),
        
        # Already Devanagari (should not change)
        ("राम", "राम"),
        ("नेपाल", "नेपाल"),
    ]
    
    passed = 0
    failed = 0
    
    for roman, expected in test_cases:
        result = smart_convert_to_devanagari(roman)
        
        # For debugging
        print(f"\nInput: '{roman}'")
        print(f"Expected: '{expected}'")
        print(f"Got: '{result}'")
        print(f"Match: {result == expected}")
        
        if result == expected:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status} | {roman:20} → {result:20}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)


def create_transliteration_demo():
    """Create a Streamlit demo app for testing transliteration."""
    st.title("🔄 Roman to Devanagari Converter (Aksharamukha)")
    st.markdown("---")
    
    # Check installation
    status = check_installation()
    
    if status['installed']:
        st.success(status['message'])
    else:
        st.error(status['message'])
        st.code(status['instructions'])
        st.stop()
    
    st.info("""
    **How to use:**
    - Type in Roman/English (e.g., 'ram', 'nepal', 'hari')
    - Type in Devanagari (e.g., 'राम', 'नेपाल')
    - The system will automatically detect and convert
    """)
    
    # Input section
    st.markdown("### Test Conversion")
    user_input = st.text_input(
        "Enter text:",
        placeholder="Type 'ram' or 'राम'...",
        help="You can type in Roman or Devanagari"
    )
    
    if user_input:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Input", user_input)
            is_dev = is_devanagari(user_input)
            is_rom = is_roman(user_input)
            st.caption(f"Devanagari: {is_dev}")
            st.caption(f"Roman: {is_rom}")
        
        with col2:
            with st.spinner("Converting..."):
                converted = smart_convert_to_devanagari(user_input)
            st.metric("Converted", converted)
            if converted == user_input:
                st.caption("✅ Already Devanagari")
            else:
                st.caption("🔄 Converted from Roman")
        
        with col3:
            st.metric("Script Type", "Devanagari" if is_devanagari(user_input) else "Roman")
            if is_roman(user_input):
                st.caption("Will be converted")
    
    # Quick test section
    st.markdown("---")
    st.subheader("Quick Test - Common Nepali Names")
    
    test_words = [
        ("ram", "राम"),
        ("sita", "सीता"),
        ("hari", "हरि"),
        ("krishna", "कृष्ण"),
        ("nepal", "नेपाल"),
        ("maya", "माया"),
    ]
    
    cols = st.columns(3)
    
    for i, (roman, expected) in enumerate(test_words):
        with cols[i % 3]:
            result = smart_convert_to_devanagari(roman)
            match = "✅" if result == expected else "❌"
            st.code(f"{match} {roman}\n→ {result}\n(expect: {expected})")
    
    # Debugging section
    st.markdown("---")
    st.subheader("🔧 Debugging Information")
    
    if st.checkbox("Show debug info"):
        st.json({
            "aksharamukha_available": AKSHARAMUKHA_AVAILABLE,
            "import_error": IMPORT_ERROR if IMPORT_ERROR else "None",
            "cache_info": "Using @st.cache_data for performance"
        })


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Check if running in Streamlit
    try:
        import streamlit as st
        create_transliteration_demo()
    except:
        # Running as regular Python script
        print("\n🔄 Roman to Devanagari Transliteration Module")
        print("Using Aksharamukha Library")
        print("=" * 70)
        test_transliteration()
        print("\nTo run the interactive demo:")
        print("  streamlit run transliteration_aksharamukha.py")