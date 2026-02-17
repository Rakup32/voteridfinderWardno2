# -*- coding: utf-8 -*-
"""
Print Logic for ZKP8016 Thermal Printer
UPDATED: Image Printing with Kalimati Font for Nepali
"""

import unicodedata
from datetime import datetime
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import io

# --- CONFIGURATION ---
# 576px is standard for 80mm paper. Use 384px for 58mm paper.
PRINTER_WIDTH = 576 
FONT_PATH = "Kalimati.otf"  # Updated to your specific font file

def normalize_text(text):
    """Normalize text for consistent display"""
    if not isinstance(text, str):
        text = str(text)
    return unicodedata.normalize('NFC', text.strip())

def get_font(size):
    """Load the Kalimati font or fallback to default if missing"""
    try:
        # ImageFont.truetype supports .otf files as well
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        # Fallback if file not found (Will not support Nepali properly)
        print(f"WARNING: Could not load {FONT_PATH}. Using default font.")
        return ImageFont.load_default()

def draw_text_wrapped(draw, text, x, y, font, max_width):
    """Helper to draw multi-line text if it exceeds width"""
    lines = []
    words = text.split()
    current_line = []
    
    for word in words:
        # Check width of adding this word
        test_line = ' '.join(current_line + [word])
        # Get width (bbox[2] is width in newer Pillow versions)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        
        if w <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    
    # Draw the lines
    current_y = y
    # Get approximate line height
    bbox = font.getbbox("Ay")
    line_height = (bbox[3] - bbox[1]) + 10 # Height + padding
    
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=0) # 0 = Black
        current_y += line_height
        
    return current_y # Return new Y position

def create_receipt_image(voter_data):
    """
    Generates a PIL Image of the receipt.
    This solves the 'Box' issue by rendering text as pixels.
    """
    # 1. Setup Canvas
    width = PRINTER_WIDTH
    height = 1000 # Temporary height
    image = Image.new('1', (width, height), 255) # '1' = 1-bit pixels (B&W), 255 = White
    draw = ImageDraw.Draw(image)
    
    # 2. Setup Fonts (Kalimati sizes)
    font_header = get_font(32)  # Large for titles
    font_sub = get_font(22)     # Medium
    font_body = get_font(20)    # Standard text
    
    y = 20 # Start Y position
    
    # 3. Draw Header
    title = "मतदाता विवरण"
    subtitle = "VOTER DETAILS"
    
    # Center Title
    w = draw.textbbox((0, 0), title, font=font_header)[2]
    draw.text(((width - w) / 2, y), title, font=font_header, fill=0)
    y += 45
    
    # Center Subtitle
    w = draw.textbbox((0, 0), subtitle, font=font_sub)[2]
    draw.text(((width - w) / 2, y), subtitle, font=font_sub, fill=0)
    y += 40
    
    # Draw Divider
    draw.line([(10, y), (width - 10, y)], fill=0, width=3)
    y += 20
    
    # 4. Draw Voter Data
    # Serial Number Box
    if 'सि.नं.' in voter_data:
        text = f"सि.नं. (Serial): {voter_data['सि.नं.']}"
        draw.text((20, y), text, font=font_body, fill=0)
        y += 35

    # Voter Number (Bold/Large)
    if 'मतदाता नं' in voter_data:
        text = f"मतदाता नं: {voter_data['मतदाता नं']}"
        draw.text((20, y), text, font=font_header, fill=0) # Larger font
        y += 45
        
    # Draw Divider
    draw.line([(10, y), (width - 10, y)], fill=0, width=1)
    y += 20
    
    # Name
    if 'मतदाताको नाम' in voter_data:
        draw.text((20, y), "नाम (Name):", font=font_body, fill=0)
        y += 30
        # Value (Wrapped)
        name = normalize_text(voter_data['मतदाताको नाम'])
        y = draw_text_wrapped(draw, name, 40, y, font_header, width - 50)
        y += 10

    # Parents
    if 'पिता/माताको नाम' in voter_data:
        draw.text((20, y), "पिता/माता (Parents):", font=font_body, fill=0)
        y += 30
        parent = normalize_text(voter_data['पिता/माताको नाम'])
        y = draw_text_wrapped(draw, parent, 40, y, font_body, width - 50)
        y += 10
        
    # Spouse
    if 'पति/पत्नीको नाम' in voter_data and voter_data['पति/पत्नीको नाम'] != '-':
        draw.text((20, y), "पति/पत्नी (Spouse):", font=font_body, fill=0)
        y += 30
        spouse = normalize_text(voter_data['पति/पत्नीको नाम'])
        y = draw_text_wrapped(draw, spouse, 40, y, font_body, width - 50)
        y += 10

    # Age/Gender
    info_line = []
    if 'उमेर(वर्ष)' in voter_data:
        info_line.append(f"उमेर: {voter_data['उमेर(वर्ष)']}")
    if 'लिङ्ग' in voter_data:
        info_line.append(f"लिङ्ग: {voter_data['लिङ्ग']}")
    
    if info_line:
        draw.text((20, y), " | ".join(info_line), font=font_body, fill=0)
        y += 35
        
    # 5. Footer
    y += 20
    draw.line([(10, y), (width - 10, y)], fill=0, width=2)
    y += 10
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((20, y), f"Print Date: {timestamp}", font=font_body, fill=0)
    y += 30
    
    # Crop the image to actual content height + padding
    final_height = y + 20
    final_image = image.crop((0, 0, width, final_height))
    
    return final_image

def show_print_dialog(voter_data):
    """
    Shows the generated image in Streamlit for printing.
    """
    st.subheader("🖨️ मुद्रण पूर्वावलोकन (Print Preview)")
    
    col1, col2 = st.columns([1, 1])
    
    # Check for font file
    if not os.path.exists(FONT_PATH):
        st.error(f"❌ Error: '{FONT_PATH}' not found!")
        st.warning(f"Please place the file '{FONT_PATH}' in the same folder as this script.")
        return

    # Generate Image
    try:
        receipt_img = create_receipt_image(voter_data)
        
        with col1:
            st.image(receipt_img, caption="Thermal Printer Output", use_container_width=True)
            
        with col2:
            st.success("✅ Image Generated with Kalimati Font")
            
            # Print Instructions
            st.markdown("""
            **To Print:**
            1. Right-click the image on the left.
            2. Select **'Open image in new tab'**.
            3. Press **Ctrl + P**.
            4. Choose **ZKP8016** printer.
            """)
            
            # Allow download
            buf = io.BytesIO()
            receipt_img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 Download Receipt Image",
                data=byte_im,
                file_name=f"voter_{voter_data.get('मतदाता नं', 'receipt')}.png",
                mime="image/png"
            )

    except Exception as e:
        st.error(f"Error creating image: {e}")