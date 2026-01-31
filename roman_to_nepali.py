"""
Roman (English) to Devanagari Nepali Transliteration
Fast, cached conversion for voter search application
"""

import functools

# Comprehensive mapping for Nepali Devanagari
VOWELS = {
    'a': 'अ', 'aa': 'आ', 'i': 'इ', 'ii': 'ई', 'u': 'उ', 'uu': 'ऊ',
    'e': 'ए', 'ai': 'ऐ', 'o': 'ओ', 'au': 'औ',
    'ri': 'ऋ', 'rii': 'ॠ',
}

# Dependent vowel forms (mātrā)
MATRA = {
    'a': '', 'aa': 'ा', 'i': 'ि', 'ii': 'ी', 'u': 'ु', 'uu': 'ू',
    'e': 'े', 'ai': 'ै', 'o': 'ो', 'au': 'ौ',
    'ri': 'ृ', 'rii': 'ॄ',
}

CONSONANTS = {
    # Velar
    'k': 'क', 'kh': 'ख', 'g': 'ग', 'gh': 'घ', 'ng': 'ङ',
    # Palatal
    'ch': 'च', 'chh': 'छ', 'j': 'ज', 'jh': 'झ', 'ny': 'ञ', 'yna': 'ञ',
    # Retroflex
    't': 'ट', 'th': 'ठ', 'd': 'ड', 'dh': 'ढ', 'n': 'ण',
    # Dental
    'ta': 'त', 'tha': 'थ', 'da': 'द', 'dha': 'ध', 'na': 'न',
    # Labial
    'p': 'प', 'ph': 'फ', 'b': 'ब', 'bh': 'भ', 'm': 'म',
    # Approximant
    'y': 'य', 'r': 'र', 'l': 'ल', 'w': 'व', 'v': 'व',
    # Sibilant
    'sh': 'श', 'shh': 'ष', 's': 'स',
    # Glottal
    'h': 'ह',
    # Additional
    'ksh': 'क्ष', 'tr': 'त्र', 'gya': 'ज्ञ', 'jnya': 'ज्ञ',
}

# Special characters
SPECIAL = {
    '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
    '5': '५', '6': '६', '7': '७', '8': '८', '9': '९',
    '.': '।', '..': '॥', ' ': ' ',
}

# Common name mappings for better accuracy
NAME_SHORTCUTS = {
    'ram': 'राम',
    'rama': 'राम',
    'shyam': 'श्याम',
    'hari': 'हरि',
    'krishna': 'कृष्ण',
    'sita': 'सीता',
    'gita': 'गीता',
    'devi': 'देवी',
    'kumar': 'कुमार',
    'prasad': 'प्रसाद',
    'bahadur': 'बहादुर',
    'kumari': 'कुमारी',
    'maya': 'माया',
    'laxmi': 'लक्ष्मी',
    'lakshmi': 'लक्ष्मी',
    'saraswati': 'सरस्वती',
    'parvati': 'पार्वती',
    'shrestha': 'श्रेष्ठ',
    'shakya': 'शाक्य',
    'tamang': 'तामाङ',
    'gurung': 'गुरुङ',
    'magar': 'मगर',
    'rai': 'राई',
    'limbu': 'लिम्बू',
    'thapa': 'थापा',
    'adhikari': 'अधिकारी',
    'khatri': 'खत्री',
    'karki': 'कार्की',
    'subedi': 'सुवेदी',
    'gautam': 'गौतम',
    'sharma': 'शर्मा',
    'aryal': 'अर्याल',
    'pandey': 'पाण्डेय',
    'poudel': 'पौडेल',
    'pokharel': 'पोखरेल',
    'regmi': 'रेग्मी',
    'rijal': 'रिजाल',
    'sapkota': 'सापकोटा',
    'bhandari': 'भण्डारी',
    'bhattarai': 'भट्टराई',
    'khadka': 'खड्का',
    'dahal': 'दाहाल',
    'nepal': 'नेपाल',
}


@functools.lru_cache(maxsize=1000)
def roman_to_devanagari(text):
    """
    Convert Roman (English) text to Devanagari Nepali script.
    Uses LRU cache for fast repeated conversions.
    
    Parameters:
    -----------
    text : str
        Roman text to convert
    
    Returns:
    --------
    str : Devanagari text
    
    Examples:
    ---------
    >>> roman_to_devanagari("ram")
    'राम'
    >>> roman_to_devanagari("krishna")
    'कृष्ण'
    >>> roman_to_devanagari("sita devi")
    'सीता देवी'
    """
    if not text:
        return text
    
    text = text.strip().lower()
    
    # Check for direct name shortcuts
    if text in NAME_SHORTCUTS:
        return NAME_SHORTCUTS[text]
    
    # Check for multi-word shortcuts
    words = text.split()
    if len(words) > 1:
        converted_words = []
        for word in words:
            if word in NAME_SHORTCUTS:
                converted_words.append(NAME_SHORTCUTS[word])
            else:
                converted_words.append(_transliterate_word(word))
        return ' '.join(converted_words)
    
    return _transliterate_word(text)


def _transliterate_word(word):
    """
    Transliterate a single word from Roman to Devanagari.
    
    Parameters:
    -----------
    word : str
        Single word to transliterate
    
    Returns:
    --------
    str : Devanagari word
    """
    if not word:
        return word
    
    result = []
    i = 0
    
    while i < len(word):
        matched = False
        
        # Try to match longest possible sequence first
        for length in range(min(4, len(word) - i), 0, -1):
            substr = word[i:i+length]
            
            # Check for special characters
            if substr in SPECIAL:
                result.append(SPECIAL[substr])
                i += length
                matched = True
                break
            
            # Check for consonant clusters (ksh, tr, gya, etc.)
            if length >= 2 and substr in CONSONANTS:
                result.append(CONSONANTS[substr])
                # Check if followed by vowel
                if i + length < len(word):
                    next_pos = i + length
                    for vlen in range(min(3, len(word) - next_pos), 0, -1):
                        vsub = word[next_pos:next_pos+vlen]
                        if vsub in MATRA:
                            result.append(MATRA[vsub])
                            i += length + vlen
                            matched = True
                            break
                    if matched:
                        break
                else:
                    result.append('्')  # Add halant if at word end
                i += length
                matched = True
                break
            
            # Check for consonant + vowel
            if length >= 2:
                for clen in range(min(3, length), 0, -1):
                    csub = substr[:clen]
                    vsub = substr[clen:]
                    if csub in CONSONANTS and vsub in MATRA:
                        result.append(CONSONANTS[csub])
                        result.append(MATRA[vsub])
                        i += length
                        matched = True
                        break
                if matched:
                    break
            
            # Check for standalone consonant
            if substr in CONSONANTS:
                result.append(CONSONANTS[substr])
                # Add inherent 'a' sound unless followed by consonant or halant
                if i + length < len(word):
                    next_char = word[i+length]
                    # Don't add inherent 'a' if next is consonant
                    peek_matched = False
                    for plen in range(min(3, len(word) - (i+length)), 0, -1):
                        peek = word[i+length:i+length+plen]
                        if peek in CONSONANTS or peek in MATRA:
                            peek_matched = True
                            break
                    if peek_matched and word[i+length:i+length+plen] in CONSONANTS:
                        result.append('्')  # Add halant before next consonant
                i += length
                matched = True
                break
            
            # Check for standalone vowel
            if substr in VOWELS:
                result.append(VOWELS[substr])
                i += length
                matched = True
                break
        
        if not matched:
            # If nothing matched, keep the original character
            result.append(word[i])
            i += 1
    
    return ''.join(result)


def is_devanagari(text):
    """
    Check if text contains Devanagari characters.
    
    Parameters:
    -----------
    text : str
        Text to check
    
    Returns:
    --------
    bool : True if text contains Devanagari
    """
    if not text:
        return False
    
    # Devanagari Unicode range: U+0900 to U+097F
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return True
    return False


def smart_convert(text):
    """
    Smart conversion: only convert if input is Roman (not already Devanagari).
    
    Parameters:
    -----------
    text : str
        Text to potentially convert
    
    Returns:
    --------
    str : Original text if already Devanagari, converted text if Roman
    """
    if not text:
        return text
    
    text = text.strip()
    
    # If already contains Devanagari, return as-is
    if is_devanagari(text):
        return text
    
    # Otherwise, convert from Roman
    return roman_to_devanagari(text)


# Quick test
if __name__ == "__main__":
    test_cases = [
        "ram",
        "krishna",
        "sita devi",
        "hari bahadur",
        "rama shyama",
        "laxmi kumari",
        "ramesh kumar shrestha",
    ]
    
    print("Roman to Devanagari Conversion Test")
    print("=" * 50)
    for test in test_cases:
        result = roman_to_devanagari(test)
        print(f"{test:25} -> {result}")
    
    print("\n" + "=" * 50)
    print("Smart Convert Test (mixed input)")
    print("=" * 50)
    
    mixed_tests = [
        "ram",           # Roman
        "राम",          # Already Devanagari
        "krishna",      # Roman
        "कृष्ण",        # Already Devanagari
    ]
    
    for test in mixed_tests:
        result = smart_convert(test)
        is_dev = "✓ Devanagari" if is_devanagari(test) else "✗ Roman"
        print(f"{test:15} ({is_dev}) -> {result}")
