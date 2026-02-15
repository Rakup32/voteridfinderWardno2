"""
Print Logic for Voter Search App - Screenshot Method
====================================================
Generates compact HTML receipts optimized for html2canvas screenshot printing.
Designed for 80mm thermal printers with proper Nepali font rendering.

Author: Voter Search System
Date: 2026-02-15
"""

from datetime import datetime
from typing import Dict, Any


def format_voter_receipt_html(voter_data: Dict[str, Any]) -> str:
    """
    Generate a compact HTML receipt for screenshot-based printing.
    
    This HTML is designed to:
    - Render properly in browser with Nepali fonts
    - Be captured as PNG via html2canvas
    - Print on 80mm thermal paper (72mm content width)
    - Use minimal paper with tight spacing
    
    Args:
        voter_data: Dictionary containing voter information with keys:
            - 'सि.नं.' (Serial Number)
            - 'मतदाता नं' (Voter Number)
            - 'मतदाताको नाम' (Voter Name)
            - 'उमेर(वर्ष)' (Age in Years)
            - 'लिङ्ग' (Gender)
            - 'पति/पत्नीको नाम' (Spouse Name)
            - 'पिता/माताको नाम' (Father/Mother Name)
    
    Returns:
        Complete HTML string with inline CSS, ready for screenshot
    """
    
    # Get current date in Nepali format
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Safely extract voter data with fallbacks
    serial_no = voter_data.get('सि.नं.', 'N/A')
    voter_no = voter_data.get('मतदाता नं', 'N/A')
    voter_name = voter_data.get('मतदाताको नाम', 'N/A')
    age = voter_data.get('उमेर(वर्ष)', 'N/A')
    gender = voter_data.get('लिङ्ग', 'N/A')
    spouse_name = voter_data.get('पति/पत्नीको नाम', 'N/A')
    parent_name = voter_data.get('पिता/माताको नाम', 'N/A')
    
    # Generate compact HTML with inline CSS
    html_content = f"""<!DOCTYPE html>
<html lang="ne">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>मतदाता विवरण</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Mangal', 'Noto Sans Devanagari', 'Arial', sans-serif;
            background-color: #ffffff;
            width: 72mm;
            padding: 3mm;
            margin: 0;
            color: #000000;
        }}
        
        .receipt {{
            width: 100%;
            background-color: #ffffff;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 2px solid #000000;
            padding-bottom: 3mm;
            margin-bottom: 3mm;
        }}
        
        .header h1 {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 2mm;
        }}
        
        .content {{
            font-size: 12px;
            line-height: 1.3;
        }}
        
        .row {{
            display: flex;
            justify-content: space-between;
            padding: 1.5mm 0;
            border-bottom: 1px dashed #cccccc;
        }}
        
        .row:last-child {{
            border-bottom: none;
        }}
        
        .label {{
            font-weight: bold;
            width: 45%;
            color: #333333;
        }}
        
        .value {{
            width: 55%;
            text-align: right;
            color: #000000;
        }}
        
        .footer {{
            margin-top: 4mm;
            padding-top: 3mm;
            border-top: 2px solid #000000;
            text-align: center;
            font-size: 10px;
            color: #666666;
        }}
        
        @media print {{
            body {{
                margin: 0;
                padding: 3mm;
            }}
            
            .receipt {{
                page-break-after: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="receipt">
        <!-- Header Section -->
        <div class="header">
            <h1>मतदाता विवरण</h1>
        </div>
        
        <!-- Content Section -->
        <div class="content">
            <div class="row">
                <span class="label">सि.नं.:</span>
                <span class="value">{serial_no}</span>
            </div>
            
            <div class="row">
                <span class="label">मतदाता नं:</span>
                <span class="value">{voter_no}</span>
            </div>
            
            <div class="row">
                <span class="label">मतदाताको नाम:</span>
                <span class="value">{voter_name}</span>
            </div>
            
            <div class="row">
                <span class="label">उमेर:</span>
                <span class="value">{age} वर्ष</span>
            </div>
            
            <div class="row">
                <span class="label">लिङ्ग:</span>
                <span class="value">{gender}</span>
            </div>
            
            <div class="row">
                <span class="label">पति/पत्नीको नाम:</span>
                <span class="value">{spouse_name}</span>
            </div>
            
            <div class="row">
                <span class="label">पिता/माताको नाम:</span>
                <span class="value">{parent_name}</span>
            </div>
        </div>
        
        <!-- Footer Section -->
        <div class="footer">
            <div>मिति: {current_date}</div>
        </div>
    </div>
</body>
</html>"""
    
    return html_content


def test_receipt_generation():
    """Test function to verify receipt HTML generation."""
    
    # Sample voter data
    test_voter = {
        'सि.नं.': '१',
        'मतदाता नं': '१२३४५',
        'मतदाताको नाम': 'राम बहादुर श्रेष्ठ',
        'उमेर(वर्ष)': '३५',
        'लिङ्ग': 'पुरुष',
        'पति/पत्नीको नाम': 'सीता श्रेष्ठ',
        'पिता/माताको नाम': 'हरि बहादुर श्रेष्ठ'
    }
    
    # Generate HTML
    html = format_voter_receipt_html(test_voter)
    
    # Save to file for testing
    with open('/home/claude/test_receipt.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Test receipt generated successfully!")
    print(f"📄 Saved to: test_receipt.html")
    print(f"📏 HTML length: {len(html)} characters")
    
    return html


if __name__ == "__main__":
    # Run test
    test_receipt_generation()