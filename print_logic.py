"""
Print Logic for 58mm/80mm Thermal Printer
Updated with QZ Tray HTML support for Nepali text
"""

import unicodedata
from datetime import datetime
import streamlit as st


def normalize_text(text):
    """Normalize text for consistent display"""
    if not isinstance(text, str):
        text = str(text)
    return unicodedata.normalize('NFC', text.strip())


def center_text(text, width=42):
    """Center text within specified width"""
    text = str(text)
    padding = (width - len(text)) // 2
    return ' ' * padding + text


def split_text(text, width=42):
    """Split text into lines of specified width"""
    text = str(text)
    lines = []
    words = text.split()
    current_line = ""
    
    for word in words:
        if len(current_line + word) + 1 <= width:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines


def format_divider(char='=', width=42):
    """Create a divider line"""
    return char * width


def format_voter_receipt(voter_data):
    """
    Format voter data for 58mm thermal printer (text mode)
    
    Parameters:
    -----------
    voter_data : dict
        Dictionary containing voter information with keys matching column names
    
    Returns:
    --------
    str : Formatted receipt text ready for printing
    """
    
    lines = []
    
    # Header
    lines.append(format_divider('='))
    lines.append(center_text("मतदाता विवरण"))
    lines.append(center_text("VOTER DETAILS"))
    lines.append(format_divider('='))
    lines.append("")
    
    # Voter Number (prominent)
    if 'मतदाता नं' in voter_data:
        lines.append(center_text(f"मतदाता नं: {voter_data['मतदाता नं']}"))
        lines.append(format_divider('-'))
    
    # Serial Number
    if 'सि.नं.' in voter_data:
        lines.append(f"सि.नं.: {voter_data['सि.नं.']}")
    
    # Voter Name (can be long, so split if needed)
    if 'मतदाताको नाम' in voter_data:
        name = normalize_text(voter_data['मतदाताको नाम'])
        lines.append("")
        lines.append("मतदाताको नाम:")
        name_lines = split_text(name, width=40)
        for nl in name_lines:
            lines.append(f"  {nl}")
    
    # Age and Gender on same line
    age_gender_line = ""
    if 'उमेर(वर्ष)' in voter_data:
        age_gender_line += f"उमेर: {voter_data['उमेर(वर्ष)']} वर्ष"
    if 'लिङ्ग' in voter_data:
        if age_gender_line:
            age_gender_line += " | "
        age_gender_line += f"लिङ्ग: {voter_data['लिङ्ग']}"
    if age_gender_line:
        lines.append("")
        lines.append(age_gender_line)
    
    # Father/Mother Name
    if 'पिता/माताको नाम' in voter_data and voter_data['पिता/माताको नाम']:
        parent = normalize_text(voter_data['पिता/माताको नाम'])
        lines.append("")
        lines.append("पिता/माताको नाम:")
        parent_lines = split_text(parent, width=40)
        for pl in parent_lines:
            lines.append(f"  {pl}")
    
    # Spouse Name
    if 'पति/पत्नीको नाम' in voter_data and voter_data['पति/पत्नीको नाम'] and voter_data['पति/पत्नीको नाम'] != '-':
        spouse = normalize_text(voter_data['पति/पत्नीको नाम'])
        lines.append("")
        lines.append("पति/पत्नीको नाम:")
        spouse_lines = split_text(spouse, width=40)
        for sl in spouse_lines:
            lines.append(f"  {sl}")
    
    # Additional details if present
    if 'मतदाता विवरणहरू' in voter_data and voter_data['मतदाता विवरणहरू']:
        details = voter_data['मतदाता विवरणहरू']
        if details != 'Print':  # Skip the button label
            lines.append("")
            lines.append(format_divider('-'))
            lines.append("अतिरिक्त विवरण:")
            detail_lines = split_text(details, width=40)
            for dl in detail_lines:
                lines.append(f"  {dl}")
    
    # Footer
    lines.append("")
    lines.append(format_divider('='))
    
    # Print timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(center_text("मुद्रण मिति / Print Date"))
    lines.append(center_text(timestamp))
    
    lines.append(format_divider('='))
    lines.append("")
    lines.append(center_text("*** धन्यवाद ***"))
    lines.append(center_text("*** Thank You ***"))
    lines.append("")
    
    # Join all lines
    return '\n'.join(lines)


def format_voter_receipt_html(voter_data):
    """
    Format voter data as SIMPLE, RELIABLE HTML for QZ Tray pixel printing.
    Optimized for perfect Nepali (Devanagari) text rendering with minimal complexity.
    
    Parameters:
    -----------
    voter_data : dict
        Dictionary containing voter information
    
    Returns:
    --------
    str : HTML string optimized for 80mm thermal printer
    """
    
    # Get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Extract and normalize all data
    serial_no = str(voter_data.get('सि.नं.', 'N/A'))
    voter_no = str(voter_data.get('मतदाता नं', 'N/A'))
    voter_name = normalize_text(voter_data.get('मतदाताको नाम', 'N/A'))
    age = str(voter_data.get('उमेर(वर्ष)', 'N/A'))
    gender = str(voter_data.get('लिङ्ग', 'N/A'))
    parent_name = normalize_text(voter_data.get('पिता/माताको नाम', 'N/A'))
    spouse_name = voter_data.get('पति/पत्नीको नाम', '')
    
    # Spouse section (only if exists)
    spouse_section = ""
    if spouse_name and str(spouse_name).strip() and str(spouse_name).strip() != '-':
        spouse_name = normalize_text(spouse_name)
        spouse_section = f'''
        <div style="margin-top:4mm; padding:2mm 0; border-top:1px dotted #999;">
            <div style="font-weight:bold; font-size:11pt;">पति/पत्नी</div>
            <div style="font-size:13pt; margin-top:1mm;">{spouse_name}</div>
        </div>'''
    
    # Simple, clean HTML with web-safe fonts
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    width: 70mm;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    padding: 4mm;
    background: white;
    color: black;
    line-height: 1.6;
}}

.header {{
    text-align: center;
    border-bottom: 3px solid black;
    padding-bottom: 3mm;
    margin-bottom: 4mm;
}}

.title {{
    font-size: 16pt;
    font-weight: bold;
    margin-bottom: 1mm;
}}

.subtitle {{
    font-size: 10pt;
    font-weight: bold;
    color: #333;
}}

.box {{
    border: 3px solid black;
    background: #f5f5f5;
    text-align: center;
    padding: 3mm;
    margin: 3mm 0;
    font-weight: bold;
    font-size: 14pt;
}}

.big-number {{
    text-align: center;
    font-size: 18pt;
    font-weight: bold;
    border-top: 2px solid black;
    border-bottom: 2px solid black;
    padding: 3mm 0;
    margin: 3mm 0;
    background: #f0f0f0;
}}

.field {{
    margin: 3mm 0;
    padding: 2mm 0;
    border-bottom: 1px dotted #999;
}}

.field-label {{
    font-weight: bold;
    font-size: 10pt;
    margin-bottom: 1mm;
}}

.field-value {{
    font-size: 13pt;
    font-weight: 600;
}}

.inline {{
    background: #f8f8f8;
    padding: 2mm;
    margin: 3mm 0;
    font-size: 11pt;
}}

.signature {{
    margin-top: 8mm;
    padding-top: 3mm;
    border-top: 2px solid #666;
}}

.sig-label {{
    font-size: 9pt;
    font-weight: bold;
    margin-bottom: 2mm;
}}

.sig-line {{
    text-align: right;
    margin-top: 10mm;
    padding-top: 2mm;
    border-top: 2px dashed black;
    font-size: 9pt;
}}

.footer {{
    text-align: center;
    margin-top: 4mm;
    padding-top: 3mm;
    border-top: 3px solid black;
}}

.time {{
    font-size: 9pt;
    color: #555;
    margin-bottom: 2mm;
}}

.thanks {{
    font-size: 11pt;
    font-weight: bold;
}}
</style>
</head>
<body>

<div class="header">
    <div class="title">मतदाता विवरण</div>
    <div class="subtitle">VOTER DETAILS</div>
</div>

<div class="box">
    सि.नं. {serial_no}
</div>

<div class="big-number">
    मतदाता नं {voter_no}
</div>

<div class="field">
    <div class="field-label">नाम</div>
    <div class="field-value">{voter_name}</div>
</div>

<div class="inline">
    <strong>उमेर</strong> {age} वर्ष | <strong>लिङ्ग</strong> {gender}
</div>

<div class="field">
    <div class="field-label">पिता/माता</div>
    <div class="field-value">{parent_name}</div>
</div>

{spouse_section}

<div class="signature">
    <div class="sig-label">हस्ताक्षर / Signature</div>
    <div class="sig-line">_______________</div>
</div>

<div class="footer">
    <div class="time">{timestamp}</div>
    <div class="thanks">धन्यवाद / Thank You</div>
</div>

</body>
</html>"""
    
    return html


def create_print_preview(voter_data):
    """
    Create a print preview in Streamlit
    
    Parameters:
    -----------
    voter_data : dict
        Dictionary containing voter information
    """
    receipt_text = format_voter_receipt(voter_data)
    
    # Display with custom styling for better visibility
    st.markdown(f"""
    <div style="
        background: #f7fafc;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow: visible;
    ">{receipt_text}</div>
    """, unsafe_allow_html=True)
    
    return receipt_text


def generate_print_button(row_data, key_suffix):
    """
    Generate a print button for a specific row
    
    Parameters:
    -----------
    row_data : pandas.Series or dict
        Row data containing voter information
    key_suffix : str
        Unique identifier for the button key
    
    Returns:
    --------
    bool : True if print button was clicked
    """
    if st.button("🖨️ Print", key=f"print_{key_suffix}"):
        return True
    return False


def show_print_dialog(voter_data):
    """
    Show print dialog with preview
    
    Parameters:
    -----------
    voter_data : dict
        Dictionary containing voter information
    """
    st.subheader("🖨️ मुद्रण पूर्वावलोकन / Print Preview")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("📄 58mm थर्मल प्रिन्टर ढाँचा (42 chars/line)")
        receipt_text = create_print_preview(voter_data)
    
    with col2:
        st.write("**मतदाता जानकारी:**")
        st.write(f"नाम: {voter_data.get('मतदाताको नाम', 'N/A')}")
        st.write(f"नं: {voter_data.get('मतदाता नं', 'N/A')}")
        
        if st.button("📥 Download TXT", use_container_width=True):
            # Create downloadable text file
            st.download_button(
                label="💾 Download Receipt",
                data=receipt_text,
                file_name=f"voter_{voter_data.get('मतदाता नं', 'receipt')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.success("✅ Ready to print!")
        st.caption("Copy text above or download to print on thermal printer")


def format_compact_receipt(voter_data):
    """
    Create a more compact version for quick printing
    
    Parameters:
    -----------
    voter_data : dict
        Dictionary containing voter information
    
    Returns:
    --------
    str : Compact formatted receipt text
    """
    lines = []
    
    lines.append(format_divider('='))
    lines.append(center_text("मतदाता विवरण"))
    lines.append(format_divider('='))
    
    if 'मतदाता नं' in voter_data:
        lines.append(f"मतदाता नं: {voter_data['मतदाता नं']}")
    
    if 'मतदाताको नाम' in voter_data:
        lines.append(f"नाम: {voter_data['मतदाताको नाम']}")
    
    info = []
    if 'उमेर(वर्ष)' in voter_data:
        info.append(f"उमेर: {voter_data['उमेर(वर्ष)']}")
    if 'लिङ्ग' in voter_data:
        info.append(f"लिङ्ग: {voter_data['लिङ्ग']}")
    if info:
        lines.append(" | ".join(info))
    
    if 'पिता/माताको नाम' in voter_data:
        lines.append(f"पिता/माता: {voter_data['पिता/माताको नाम']}")
    
    lines.append(format_divider('='))
    lines.append(center_text(datetime.now().strftime("%Y-%m-%d %H:%M")))
    lines.append("")
    
    return '\n'.join(lines)


# Test function
if __name__ == "__main__":
    # Sample voter data for testing
    sample_voter = {
        'सि.नं.': 1,
        'मतदाता नं': 17641638,
        'मतदाताको नाम': 'राम बहादुर श्रेष्ठ',
        'उमेर(वर्ष)': 45,
        'लिङ्ग': 'पुरुष',
        'पति/पत्नीको नाम': 'सीता श्रेष्ठ',
        'पिता/माताको नाम': 'हरि बहादुर / सरस्वती देवी',
        'मतदाता विवरणहरू': 'Active voter'
    }
    
    print("=" * 50)
    print("THERMAL PRINTER TEST OUTPUT")
    print("=" * 50)
    print(format_voter_receipt(sample_voter))
    print("\n\n")
    print("=" * 50)
    print("COMPACT VERSION")
    print("=" * 50)
    print(format_compact_receipt(sample_voter))