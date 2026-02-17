# -*- coding: utf-8 -*-
"""
Print Logic for ZKP8016 Thermal Printer
UPDATED: "Safe Mode" - Uses Unicode Escapes for Labels to prevent 'Box' issues
"""

import unicodedata
from datetime import datetime
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import io

# --- CONFIGURATION ---
PRINTER_WIDTH = 576 
FONT_PATH = "Kalimati.otf"

# --- SAFE LABELS (Encoded to prevent corruption) ---
# These are the Nepali strings converted to safe Python code
L_HEADER = "\u092e\u0924\u0926\u093e\u0924\u093e \u0935\u093f\u0935\u0930\u0923" # मतदाता विवरण
L_SERIAL = "\u0938\u093f.\u0928\u0902." # सि.नं.
L_VOTER_NO = "\u092e\u0924\u0926\u093e\u0924\u093e \u0928\u0902" # मतदाता नं
L_NAME = "\u0928\u093e\u092e" # नाम
L_PARENTS = "\u092a\u093f\u0924\u093e/\u092e\u093e\u0924\u093e" # पिता/माता
L_SPOUSE = "\u092a\u0924\u093f/\u092a\u0924\u094d\u0928\u0940" # पति/पत्नी
L_AGE = "\u0909\u092e\u0947\u0930" # उमेर
L_GENDER = "\u0932\u093f\u0919\u094d\u0917" # लिङ्ग

def normalize_text(text):
    if not isinstance(text, str):
        text = str(text)
    return unicodedata.normalize('NFC', text.strip())

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()

def draw_text_wrapped(draw, text, x, y, font, max_width):
    lines = []
    words = text.split()
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    
    current_y = y
    bbox = font.getbbox("Ay")
    line_height = (bbox[3] - bbox[1]) + 10 
    
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=0)
        current_y += line_height
    return current_y

def create_receipt_image(voter_data):
    # 1. Setup Canvas
    width = PRINTER_WIDTH
    height = 1000
    image = Image.new('1', (width, height), 255)
    draw = ImageDraw.Draw(image)
    
    # 2. Fonts
    font_header = get_font(32)
    font_sub = get_font(22)
    font_body = get_font(20)
    
    y = 20
    
    # 3. Header
    # L_HEADER = "मतदाता विवरण"
    w = draw.textbbox((0, 0), L_HEADER, font=font_header)[2]
    draw.text(((width - w) / 2, y), L_HEADER, font=font_header, fill=0)
    y += 45
    
    subtitle = "VOTER DETAILS"
    w = draw.textbbox((0, 0), subtitle, font=font_sub)[2]
    draw.text(((width - w) / 2, y), subtitle, font=font_sub, fill=0)
    y += 40
    
    draw.line([(10, y), (width - 10, y)], fill=0, width=3)
    y += 20
    
    # 4. Data
    # Serial
    if 'सि.नं.' in voter_data:
        text = f"{L_SERIAL}: {voter_data['सि.नं.']}"
        draw.text((20, y), text, font=font_body, fill=0)
        y += 35

    # Voter No
    if 'मतदाता नं' in voter_data:
        text = f"{L_VOTER_NO}: {voter_data['मतदाता नं']}"
        draw.text((20, y), text, font=font_header, fill=0)
        y += 45
        
    draw.line([(10, y), (width - 10, y)], fill=0, width=1)
    y += 20
    
    # Name
    if 'मतदाताको नाम' in voter_data:
        draw.text((20, y), f"{L_NAME}:", font=font_body, fill=0)
        y += 30
        name = normalize_text(voter_data['मतदाताको नाम'])
        y = draw_text_wrapped(draw, name, 40, y, font_header, width - 50)
        y += 10

    # Parents
    if 'पिता/माताको नाम' in voter_data:
        draw.text((20, y), f"{L_PARENTS}:", font=font_body, fill=0)
        y += 30
        parent = normalize_text(voter_data['पिता/माताको नाम'])
        y = draw_text_wrapped(draw, parent, 40, y, font_body, width - 50)
        y += 10
        
    # Spouse
    if 'पति/पत्नीको नाम' in voter_data and voter_data['पति/पत्नीको नाम'] != '-':
        draw.text((20, y), f"{L_SPOUSE}:", font=font_body, fill=0)
        y += 30
        spouse = normalize_text(voter_data['पति/पत्नीको नाम'])
        y = draw_text_wrapped(draw, spouse, 40, y, font_body, width - 50)
        y += 10

    # Age/Gender
    info_line = []
    if 'उमेर(वर्ष)' in voter_data:
        info_line.append(f"{L_AGE}: {voter_data['उमेर(वर्ष)']}")
    if 'लिङ्ग' in voter_data:
        info_line.append(f"{L_GENDER}: {voter_data['लिङ्ग']}")
    
    if info_line:
        draw.text((20, y), " | ".join(info_line), font=font_body, fill=0)
        y += 35
        
    # 5. Footer
    y += 20
    draw.line([(10, y), (width - 10, y)], fill=0, width=2)
    y += 10
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((20, y), f"Date: {timestamp}", font=font_body, fill=0)
    y += 30
    
    final_image = image.crop((0, 0, width, y + 20))
    return final_image

def show_print_dialog(voter_data):
    st.subheader("🖨️ Print Preview")
    col1, col2 = st.columns([1, 1])
    
    if not os.path.exists(FONT_PATH):
        st.error(f"❌ '{FONT_PATH}' not found! Please upload it.")
        return

    try:
        receipt_img = create_receipt_image(voter_data)
        with col1:
            st.image(receipt_img, caption="Thermal Printer Output")
        with col2:
            st.success("✅ Ready to Print")
            buf = io.BytesIO()
            receipt_img.save(buf, format="PNG")
            st.download_button(
                label="📥 Download Image",
                data=buf.getvalue(),
                file_name="receipt.png",
                mime="image/png"
            )
    except Exception as e:
        st.error(f"Error: {e}")