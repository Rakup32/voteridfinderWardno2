"""
Print Logic Module - Screenshot-Based Printing for Nepali Text
================================================================
This module provides HTML receipt generation optimized for screenshot
printing via html2canvas and QZ Tray.

Key Features:
- Compact 72mm layout for 80mm thermal printers
- White background (critical for screenshot capture)
- Nepali font support (Mangal)
- No signature section
- Minimal margins to save paper

Author: Voter Search System
Date: 2026-02-15
"""

from datetime import datetime
from typing import Dict, Any


def format_voter_receipt_html(voter_data: Dict[str, Any]) -> str:
    """
    Generate compact HTML receipt for screenshot printing.
    
    This HTML is designed to be:
    1. Rendered in browser
    2. Captured as PNG via html2canvas
    3. Sent to thermal printer via QZ Tray
    
    Args:
        voter_data: Dictionary containing voter information
        
    Returns:
        HTML string with inline CSS, optimized for 80mm thermal printer
    """
    
    # Extract voter data with safe defaults
    serial_no = voter_data.get('सि.नं.', 'N/A')
    voter_no = voter_data.get('मतदाता नं', 'N/A')
    voter_name = voter_data.get('मतदाताको नाम', 'N/A')
    age = voter_data.get('उमेर(वर्ष)', 'N/A')
    gender = voter_data.get('लिङ्ग', 'N/A')
    spouse_name = voter_data.get('पति/पत्नीको नाम', 'N/A')
    parent_name = voter_data.get('पिता/माताको नाम', 'N/A')
    
    # Get current date in Nepali format
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Generate compact HTML with inline CSS
    html_content = f"""<!DOCTYPE html>
<html lang="ne">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>मतदाता रसिद</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            margin: 0;
            padding: 0;
            background-color: #ffffff;
        }}
        
        .receipt-container {{
            width: 72mm;
            background-color: #ffffff;
            padding: 4mm 2mm;
            font-family: 'Mangal', 'Noto Sans Devanagari', 'Arial', sans-serif;
            color: #000000;
            font-size: 11pt;
            line-height: 1.3;
        }}
        
        .receipt-header {{
            text-align: center;
            border-bottom: 2px solid #000000;
            padding-bottom: 3mm;
            margin-bottom: 3mm;
        }}
        
        .receipt-header h2 {{
            font-size: 14pt;
            font-weight: bold;
            margin-bottom: 1mm;
        }}
        
        .receipt-header .subtitle {{
            font-size: 10pt;
            color: #333333;
        }}
        
        .info-grid {{
            margin: 2mm 0;
        }}
        
        .info-row {{
            display: flex;
            padding: 1.5mm 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .info-row:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            width: 45%;
            font-weight: bold;
            font-size: 10pt;
            color: #333333;
        }}
        
        .info-value {{
            width: 55%;
            font-size: 10pt;
            color: #000000;
            word-wrap: break-word;
        }}
        
        .receipt-footer {{
            margin-top: 4mm;
            padding-top: 3mm;
            border-top: 2px solid #000000;
            text-align: center;
            font-size: 9pt;
            color: #666666;
        }}
        
        .print-date {{
            margin-top: 2mm;
            font-size: 8pt;
        }}
    </style>
</head>
<body>
    <div class="receipt-container">
        <!-- Header Section -->
        <div class="receipt-header">
            <h2>मतदाता विवरण</h2>
            <div class="subtitle">Voter Information</div>
        </div>
        
        <!-- Voter Information Grid -->
        <div class="info-grid">
            <div class="info-row">
                <div class="info-label">सि.नं.:</div>
                <div class="info-value">{serial_no}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">मतदाता नं:</div>
                <div class="info-value">{voter_no}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">नाम:</div>
                <div class="info-value">{voter_name}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">उमेर:</div>
                <div class="info-value">{age} वर्ष</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">लिङ्ग:</div>
                <div class="info-value">{gender}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">पति/पत्नी:</div>
                <div class="info-value">{spouse_name}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">पिता/माता:</div>
                <div class="info-value">{parent_name}</div>
            </div>
        </div>
        
        <!-- Footer Section -->
        <div class="receipt-footer">
            <div>धन्यवाद | Thank You</div>
            <div class="print-date">मिति: {current_date}</div>
        </div>
    </div>
</body>
</html>"""
    
    return html_content


def get_available_printers() -> list:
    """
    Placeholder function for printer discovery.
    In production, this would query QZ Tray for available printers.
    
    Returns:
        List of available printer names
    """
    # This will be populated by QZ Tray in the frontend
    return []


def validate_printer_name(printer_name: str) -> bool:
    """
    Validate printer name format.
    
    Args:
        printer_name: Name of the printer
        
    Returns:
        True if valid, False otherwise
    """
    if not printer_name or not printer_name.strip():
        return False
    
    # Basic validation - printer name should not be empty
    return len(printer_name.strip()) > 0


def test_receipt_generation():
    """Test function to verify HTML generation."""
    
    test_voter = {
        'सि.नं.': '1',
        'मतदाता नं': '123456',
        'मतदाताको नाम': 'राम बहादुर श्रेष्ठ',
        'उमेर(वर्ष)': '45',
        'लिङ्ग': 'पुरुष',
        'पति/पत्नीको नाम': 'सीता श्रेष्ठ',
        'पिता/माताको नाम': 'हरि बहादुर श्रेष्ठ'
    }
    
    html = format_voter_receipt_html(test_voter)
    
    print("=" * 70)
    print("TEST: HTML Receipt Generation")
    print("=" * 70)
    print("\nGenerated HTML:")
    print(html)
    print("\n" + "=" * 70)
    print("✅ HTML generation successful!")
    print(f"HTML length: {len(html)} characters")
    print("=" * 70)
    
    return html


if __name__ == "__main__":
    # Run test when module is executed directly
    test_receipt_generation()