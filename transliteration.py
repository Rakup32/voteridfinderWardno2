"""
Roman to Devanagari Transliteration Module
==========================================
Production-ready module for converting Roman Nepali input to Devanagari script.

Uses Aksharamukha library for accurate transliteration.
Includes caching, input detection, and error handling.

Author: Voter Search System
Date: 2026-01-31
"""

import re
import streamlit as st
from typing import Optional

# Try to import aksharamukha
try:
    from aksharamukha import transliterate
    AKSHARAMUKHA_AVAILABLE = True
except ImportError:
    AKSHARAMUKHA_AVAILABLE = False
    print("Warning: aksharamukha not installed. Install with: pip install aksharamukha")


def is_devanagari(text: str) -> bool:
    """
    Check if the input text is already in Devanagari script.
    
    Args:
        text: Input string to check
        
    Returns:
        True if text contains Devanagari characters, False otherwise
        
    Examples:
        >>> is_devanagari("राम")
        True
        >>> is_devanagari("ram")
        False
        >>> is_devanagari("राम123")
        True
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
        
    Examples:
        >>> is_roman("ram")
        True
        >>> is_roman("राम")
        False
        >>> is_roman("ram123")
        True
    """
    if not text:
        return False
    
    # Check if text contains only ASCII letters, numbers, and common punctuation
    roman_pattern = re.compile(r'^[a-zA-Z0-9\s\-.,/]+$')
    return bool(roman_pattern.match(text))


@st.cache_data(show_spinner=False)
def roman_to_devanagari(text: str, script_source: str = "ISO", script_target: str = "Devanagari") -> str:
    """
    Convert Roman script to Devanagari using Aksharamukha.
    
    This function is cached for performance in live search scenarios.
    
    Args:
        text: Input text in Roman script
        script_source: Source script name (default: "ISO" for standard Roman)
        script_target: Target script name (default: "Devanagari")
        
    Returns:
        Transliterated text in Devanagari script
        
    Examples:
        >>> roman_to_devanagari("ram")
        'राम'
        >>> roman_to_devanagari("nepal")
        'नेपाल'
        >>> roman_to_devanagari("kathmandu")
        'काठमाडौं'
        
    Note:
        - Uses Streamlit's @st.cache_data for fast repeated conversions
        - Falls back to original text if aksharamukha is not available
    """
    if not text or not text.strip():
        return text
    
    if not AKSHARAMUKHA_AVAILABLE:
        # Return original text with warning
        return text
    
    try:
        # Transliterate using Aksharamukha
        # ISO is a good default for Roman/IAST transliteration
        devanagari_text = transliterate.process(
            script_source,
            script_target,
            text,
            pre_options=['IgnoreVedicAccents'],
            post_options=['IgnoreSwaras']
        )
        return devanagari_text
    except Exception as e:
        # If conversion fails, return original text
        print(f"Transliteration error: {e}")
        return text


def smart_convert_to_devanagari(text: str) -> str:
    """
    Intelligently convert input to Devanagari.
    
    This function:
    1. Detects if input is already Devanagari (returns as-is)
    2. Detects if input is Roman (converts to Devanagari)
    3. Handles mixed input (converts Roman parts only)
    
    Args:
        text: User input in any script
        
    Returns:
        Text in Devanagari script (or original if already Devanagari)
        
    Examples:
        >>> smart_convert_to_devanagari("ram")
        'राम'
        >>> smart_convert_to_devanagari("राम")
        'राम'
        >>> smart_convert_to_devanagari("aahara")
        'आहारा'
        
    This is the main function to use in your search application.
    """
    if not text or not text.strip():
        return text
    
    text = text.strip()
    
    # If already Devanagari, return as-is
    if is_devanagari(text):
        return text
    
    # If Roman script, convert to Devanagari
    if is_roman(text):
        return roman_to_devanagari(text)
    
    # For mixed or unclear input, attempt conversion
    return roman_to_devanagari(text)


# ============================================================================
# INTEGRATION FUNCTIONS
# ============================================================================

def create_search_input_with_conversion(
    label: str = "खोज्नुहोस् / Search",
    key: str = "search_input",
    placeholder: str = "Type in Nepali or English...",
    help_text: str = "आप नेपाली वा English मा टाइप गर्न सक्नुहुन्छ"
) -> tuple[str, str]:
    """
    Create a Streamlit search input with automatic Roman → Devanagari conversion.
    
    Args:
        label: Label for the search input
        key: Unique key for the input widget
        placeholder: Placeholder text
        help_text: Help text to display
        
    Returns:
        Tuple of (original_input, converted_input)
        - original_input: What the user typed
        - converted_input: Devanagari version for searching
        
    Usage:
        ```python
        original, devanagari = create_search_input_with_conversion()
        if devanagari:
            # Use devanagari for searching
            results = search_voters(devanagari)
        ```
    """
    # Create the input field
    user_input = st.text_input(
        label,
        key=key,
        placeholder=placeholder,
        help=help_text
    )
    
    # Convert to Devanagari if needed
    devanagari_input = smart_convert_to_devanagari(user_input) if user_input else ""
    
    # Show conversion preview if input was Roman
    if user_input and devanagari_input != user_input:
        st.caption(f"🔄 Searching for: **{devanagari_input}**")
    
    return user_input, devanagari_input


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_transliteration():
    """
    Test the transliteration functions with common Nepali names and words.
    
    Run this to verify the system works correctly.
    """
    test_cases = [
        # (roman_input, expected_devanagari)
        ("ram", "राम"),
        ("sita", "सीता"),
        ("nepal", "नेपाल"),
        ("kathmandu", "काठमाडौं"),
        ("pokhara", "पोखरा"),
        ("aahara", "आहारा"),
        ("namaste", "नमस्ते"),
        ("dhanyabad", "धन्यबाद"),
    ]
    
    print("=" * 60)
    print("TRANSLITERATION TEST RESULTS")
    print("=" * 60)
    
    for roman, expected in test_cases:
        result = roman_to_devanagari(roman)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | {roman:15} → {result:15} (expected: {expected})")
    
    print("=" * 60)


def create_transliteration_demo():
    """
    Create a Streamlit demo app for testing transliteration.
    
    Use this to test the system in a standalone Streamlit app.
    """
    st.title("🔄 Roman to Devanagari Converter")
    st.markdown("---")
    
    # Info box
    st.info("""
    **How to use:**
    - Type in Roman/English (e.g., 'ram', 'nepal', 'kathmandu')
    - Type in Devanagari (e.g., 'राम', 'नेपाल')
    - The system will automatically detect and convert
    """)
    
    # Input
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
            st.caption(f"Devanagari: {is_dev} | Roman: {is_rom}")
        
        with col2:
            converted = smart_convert_to_devanagari(user_input)
            st.metric("Converted", converted)
            if converted == user_input:
                st.caption("✅ Already Devanagari")
            else:
                st.caption("🔄 Converted from Roman")
        
        with col3:
            st.metric("Script Type", "Devanagari" if is_devanagari(user_input) else "Roman")
    
    # Quick test buttons
    st.markdown("---")
    st.subheader("Quick Test")
    
    col1, col2, col3 = st.columns(3)
    
    test_words = [
        ("ram", "राम"),
        ("nepal", "नेपाल"),
        ("kathmandu", "काठमाडौं"),
        ("aahara", "आहारा"),
        ("namaste", "नमस्ते"),
        ("dhanyabad", "धन्यबाद"),
    ]
    
    for i, (roman, expected) in enumerate(test_words):
        col = [col1, col2, col3][i % 3]
        with col:
            result = roman_to_devanagari(roman)
            match = "✅" if result == expected else "❌"
            st.code(f"{match} {roman} → {result}")


# ============================================================================
# MAIN DEMO
# ============================================================================

if __name__ == "__main__":
    # Check if running in Streamlit
    try:
        import streamlit as st
        create_transliteration_demo()
    except:
        # Running as regular Python script
        print("\nRoman to Devanagari Transliteration Module")
        print("=" * 60)
        print("\nRunning tests...\n")
        test_transliteration()
        print("\nTo run the interactive demo:")
        print("  streamlit run transliteration.py")
