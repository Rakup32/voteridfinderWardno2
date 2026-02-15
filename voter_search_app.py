"""
Voter Search Application - SCREENSHOT PRINTING VERSION
======================================================
Complete integration with Roman to Nepali conversion + Screenshot printing.

Features:
- ✅ Search in English or Nepali
- ✅ Uses indic-transliteration + custom converter
- ✅ Screenshot-based printing (html2canvas + QZ Tray)
- ✅ Compact 80mm thermal receipt format
- ✅ No font corruption issues
- ✅ Production-ready

Author: Voter Search System
Date: 2026-02-15
"""

import logging
import unicodedata
import pandas as pd
import streamlit as st
import base64
import time
import extra_streamlit_components as stx
from credentials import USERNAME, PASSWORD
from print_logic import format_voter_receipt_html

# ============================================================================
# IMPORT NEPALI CONVERTER
# ============================================================================

from nepali_converter import smart_convert_to_nepali, is_devanagari, is_roman, check_installation

def _normalize_unicode(s):
    """Normalize to NFC for consistent Unicode-aware Nepali character comparison."""
    if not isinstance(s, str) or not s:
        return s
    return unicodedata.normalize("NFC", s.strip().lower())


# ============================================================================
# NEW SCREENSHOT-BASED PRINTING FUNCTION
# ============================================================================

def print_receipt_qz(printer_name: str, html_content: str):
    """
    Print voter receipt using QZ Tray with html2canvas screenshot method.
    
    This function:
    1. Encodes HTML as base64 to preserve Nepali text
    2. Injects JavaScript that:
       - Loads QZ Tray and html2canvas libraries
       - Decodes and renders HTML in a hidden div
       - Captures screenshot as PNG using html2canvas
       - Sends PNG to QZ Tray as base64 image
    
    Parameters:
    -----------
    printer_name : str
        Name of the thermal printer (e.g., 'ZKTeco ZKP8016')
    html_content : str
        HTML string with Nepali text (from format_voter_receipt_html)
    """
    
    # Encode HTML as base64 to prevent Unicode corruption
    html_base64 = base64.b64encode(html_content.encode('utf-8')).decode('ascii')
    
    # JavaScript code for screenshot printing
    qz_print_js = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Printing...</title>
        <script src="https://cdn.jsdelivr.net/npm/qz-tray@2.2/qz-tray.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>
            body {{
                font-family: 'Mangal', 'Noto Sans Devanagari', 'Arial', sans-serif;
                background-color: #f0f2f6;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            
            .status-container {{
                text-align: center;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 500px;
                width: 100%;
            }}
            
            .spinner {{
                width: 50px;
                height: 50px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #2c5aa0;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            
            .status-text {{
                color: #333;
                font-size: 16px;
                margin: 10px 0;
            }}
            
            .printer-name {{
                color: #2c5aa0;
                font-weight: bold;
            }}
            
            #receipt-container {{
                position: absolute;
                left: -9999px;
                top: 0;
                background-color: #ffffff;
            }}
            
            .success {{
                color: #28a745;
            }}
            
            .error {{
                color: #dc3545;
            }}
        </style>
    </head>
    <body>
        <div class="status-container">
            <h2 id="status-title">🖨️ Printing Receipt</h2>
            <div class="spinner" id="spinner"></div>
            <p class="status-text" id="status-message">
                Connecting to QZ Tray and printer: <span class="printer-name">{printer_name}</span>
            </p>
        </div>
        
        <!-- Hidden container for HTML rendering -->
        <div id="receipt-container"></div>
        
        <script>
        (function() {{
            console.log('🖨️ Screenshot Print Script Started');
            
            // Configuration
            const PRINTER_NAME = "{printer_name}";
            const HTML_BASE64 = "{html_base64}";
            
            // Status update functions
            function updateStatus(message, isSpinning = true) {{
                document.getElementById('status-message').innerHTML = message;
                document.getElementById('spinner').style.display = isSpinning ? 'block' : 'none';
            }}
            
            function showSuccess(message) {{
                document.getElementById('status-title').className = 'success';
                document.getElementById('status-title').textContent = '✅ Success';
                updateStatus(message, false);
            }}
            
            function showError(message) {{
                document.getElementById('status-title').className = 'error';
                document.getElementById('status-title').textContent = '❌ Error';
                updateStatus(message, false);
            }}
            
            // Decode base64 HTML
            function decodeHTML(base64) {{
                try {{
                    const decoded = atob(base64);
                    const bytes = new Uint8Array(decoded.length);
                    for (let i = 0; i < decoded.length; i++) {{
                        bytes[i] = decoded.charCodeAt(i);
                    }}
                    return new TextDecoder('utf-8').decode(bytes);
                }} catch (error) {{
                    console.error('❌ HTML decode error:', error);
                    throw new Error('Failed to decode HTML content');
                }}
            }}
            
            // Connect to QZ Tray
            async function connectQZ() {{
                updateStatus('Step 1/4: Connecting to QZ Tray...');
                
                if (qz.websocket.isActive()) {{
                    console.log('✅ QZ Tray already connected');
                    return;
                }}
                
                try {{
                    await qz.websocket.connect();
                    console.log('✅ QZ Tray connected');
                }} catch (error) {{
                    console.error('❌ QZ Connection failed:', error);
                    throw new Error('Cannot connect to QZ Tray. Please ensure it is running.');
                }}
            }}
            
            // Find printer
            async function findPrinter() {{
                updateStatus('Step 2/4: Finding printer: <span class="printer-name">' + PRINTER_NAME + '</span>');
                
                try {{
                    const found = await qz.printers.find(PRINTER_NAME);
                    console.log('✅ Printer found:', found);
                    return found;
                }} catch (error) {{
                    console.error('❌ Printer not found:', error);
                    throw new Error('Printer "' + PRINTER_NAME + '" not found');
                }}
            }}
            
            // Render HTML and capture screenshot
            async function captureScreenshot() {{
                updateStatus('Step 3/4: Rendering receipt and capturing screenshot...');
                
                try {{
                    // Decode HTML
                    const htmlContent = decodeHTML(HTML_BASE64);
                    console.log('✅ HTML decoded, length:', htmlContent.length);
                    
                    // Inject HTML into hidden container
                    const container = document.getElementById('receipt-container');
                    container.innerHTML = htmlContent;
                    
                    // Wait for fonts to load
                    await document.fonts.ready;
                    console.log('✅ Fonts loaded');
                    
                    // Wait a bit more for rendering
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    // Find the receipt element
                    const receiptElement = container.querySelector('.receipt') || 
                                          container.querySelector('body') || 
                                          container.firstElementChild;
                    
                    if (!receiptElement) {{
                        throw new Error('Receipt element not found in HTML');
                    }}
                    
                    console.log('📸 Capturing screenshot...');
                    
                    // Capture using html2canvas
                    const canvas = await html2canvas(receiptElement, {{
                        scale: 2,
                        backgroundColor: '#ffffff',
                        logging: true,
                        useCORS: true,
                        allowTaint: true
                    }});
                    
                    console.log('✅ Screenshot captured:', canvas.width, 'x', canvas.height);
                    
                    // Convert canvas to base64 PNG
                    const imageBase64 = canvas.toDataURL('image/png').split(',')[1];
                    console.log('✅ Image base64 length:', imageBase64.length);
                    
                    return imageBase64;
                    
                }} catch (error) {{
                    console.error('❌ Screenshot capture failed:', error);
                    throw new Error('Failed to capture receipt screenshot: ' + error.message);
                }}
            }}
            
            // Print image via QZ Tray
            async function printImage(printerName, imageBase64) {{
                updateStatus('Step 4/4: Sending print job to printer...');
                
                try {{
                    const config = qz.configs.create(printerName);
                    
                    const data = [{{
                        type: 'pixel',
                        format: 'image',
                        flavor: 'base64',
                        data: imageBase64
                    }}];
                    
                    console.log('🖨️ Sending image to printer...');
                    await qz.print(config, data);
                    console.log('✅ Print job completed');
                    
                }} catch (error) {{
                    console.error('❌ Print job failed:', error);
                    throw new Error('Print job failed: ' + error.message);
                }}
            }}
            
            // Main execution
            async function executePrint() {{
                try {{
                    // Step 1: Connect to QZ Tray
                    await connectQZ();
                    
                    // Step 2: Find printer
                    const printer = await findPrinter();
                    
                    // Step 3: Capture screenshot
                    const imageBase64 = await captureScreenshot();
                    
                    // Step 4: Print
                    await printImage(printer, imageBase64);
                    
                    // Success!
                    showSuccess('Receipt printed successfully! ✅');
                    
                    // Auto-close after 2 seconds
                    setTimeout(() => {{
                        window.close();
                    }}, 2000);
                    
                }} catch (error) {{
                    console.error('❌ Print process failed:', error);
                    showError(error.message || 'Print failed');
                }}
            }}
            
            // Execute when page loads
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', executePrint);
            }} else {{
                executePrint();
            }}
        }})();
        </script>
    </body>
    </html>
    """
    
    # Display the printing interface in Streamlit
    st.components.v1.html(qz_print_js, height=400, scrolling=False)


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0


# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data(show_spinner="📂 डाटा लोड भइरहेको छ...")
def load_voter_data(filepath='voterlist.xlsx'):
    """Load and preprocess voter data with caching."""
    try:
        df = pd.read_excel(filepath, engine='openpyxl')
        logger.info(f"✅ Loaded {len(df)} records from {filepath}")
        
        # Normalize string columns for search
        if 'मतदाताको नाम' in df.columns:
            df['मतदाताको नाम_lower'] = df['मतदाताको नाम'].apply(_normalize_unicode)
        if 'पिता/माताको नाम' in df.columns:
            df['पिता/माताको नाम_lower'] = df['पिता/माताको नाम'].apply(_normalize_unicode)
        if 'पति/पत्नीको नाम' in df.columns:
            df['पति/पत्नीको नाम_lower'] = df['पति/पत्नीको नाम'].apply(_normalize_unicode)
        
        return df
    except FileNotFoundError:
        st.error("❌ voterlist.xlsx फाइल भेटिएन")
        logger.error(f"File not found: {filepath}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        logger.exception("Error loading voter data")
        return pd.DataFrame()


# ============================================================================
# UNICODE-AWARE SEARCH FUNCTIONS
# ============================================================================

@st.cache_data(show_spinner=False)
def unicode_prefix_search(df, column, search_term):
    """
    Unicode-aware prefix search with automatic Nepali conversion.
    Supports both Roman and Devanagari input.
    """
    if search_term.strip() == "":
        return df
    
    # Convert search term to Nepali
    nepali_term = smart_convert_to_nepali(search_term)
    normalized_term = _normalize_unicode(nepali_term)
    
    logger.info(f"🔍 Search: '{search_term}' → '{nepali_term}' (normalized: '{normalized_term}')")
    
    # Use pre-computed lowercase column for search
    lowercase_col = f"{column}_lower"
    if lowercase_col not in df.columns:
        df[lowercase_col] = df[column].apply(_normalize_unicode)
    
    mask = df[lowercase_col].str.startswith(normalized_term, na=False)
    result = df[mask]
    
    logger.info(f"✅ Found {len(result)} matches")
    return result


def show_conversion_indicator(original, converted):
    """Show conversion status indicator."""
    if original != converted:
        st.info(f"🔄 Converted: '{original}' → '{converted}'")


# ============================================================================
# LOGIN PAGE
# ============================================================================

def login_page():
    """Display login page with authentication."""
    st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>मतदाता सूची प्रणाली / Voter List System</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.login_attempts >= 3:
            st.error("❌ Too many failed attempts. Please refresh the page.")
            return
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", key="username_input")
            password = st.text_input("🔑 Password", type="password", key="password_input")
            submit = st.form_submit_button("🔓 Login", use_container_width=True)
            
            if submit:
                if username == USERNAME and password == PASSWORD:
                    st.session_state.logged_in = True
                    st.session_state.login_attempts = 0
                    st.success("✅ Login successful!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    remaining = 3 - st.session_state.login_attempts
                    st.error(f"❌ Invalid credentials. {remaining} attempts remaining.")
        
        st.caption("💡 Set credentials in .env file or environment variables")


# ============================================================================
# DISPLAY RESULTS WITH PRINT SUPPORT
# ============================================================================

def display_results(df, display_columns):
    """Display search results with print button for each row."""
    if df.empty:
        st.warning("⚠️ No results to display")
        return
    
    # Display the dataframe
    st.dataframe(df[display_columns], use_container_width=True, hide_index=False)
    
    # Print buttons section
    st.markdown("---")
    st.subheader("🖨️ Print Receipts")
    
    # Printer configuration
    col1, col2 = st.columns([3, 1])
    with col1:
        printer_name = st.text_input(
            "Printer Name:",
            value="ZKTeco ZKP8016",
            help="Enter the exact printer name as shown in your system",
            key="printer_name_input"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 List Printers", help="Show available printers"):
            st.info("Use QZ Tray's printer list feature to find your printer name")
    
    # Print individual receipts
    st.markdown("**Select a voter to print:**")
    
    # Create print buttons for each voter
    for idx, row in df.iterrows():
        voter_name = row.get('मतदाताको नाम', 'Unknown')
        voter_no = row.get('मतदाता नं', 'N/A')
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{voter_name}** (Voter #: {voter_no})")
        with col2:
            if st.button(f"🖨️ Print", key=f"print_{idx}"):
                with st.spinner("Preparing receipt..."):
                    # Generate HTML receipt
                    html_content = format_voter_receipt_html(row.to_dict())
                    
                    # Show preview
                    with st.expander("📄 Preview Receipt"):
                        st.components.v1.html(html_content, height=400, scrolling=True)
                    
                    # Print using QZ Tray with screenshot method
                    st.markdown("---")
                    st.info("🖨️ Opening print dialog...")
                    print_receipt_qz(printer_name, html_content)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main_app():
    """Main application interface after login."""
    
    # Header with logout button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📋 मतदाता सूची खोज प्रणाली")
        st.caption("Voter List Search System • Roman/English Support")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.markdown("---")
    
    # Check conversion status
    status = check_installation()
    if status['installed']:
        st.sidebar.success("✅ Roman-Nepali converter active")
    else:
        st.sidebar.warning("⚠️ Converter not available")
    
    try:
        # Load data
        df = load_voter_data()
        if df.empty:
            st.error("❌ No data loaded")
            return
        
        # Display columns
        display_columns = [col for col in df.columns if not col.endswith('_lower')]
        
        # Sidebar options
        st.sidebar.title("🔍 खोज विकल्प / Search Options")
        
        search_options = [
            "मतदाताको नामबाट खोज्नुहोस्",
            "मतदाता नंबरबाट खोज्नुहोस्",
            "पिता/माताको नामबाट खोज्नुहोस्",
            "पति/पत्नीको नामबाट खोज्नुहोस्",
            "उन्नत खोज",
            "लिङ्गबाट फिल्टर गर्नुहोस्",
            "उमेर दायराबाट खोज्नुहोस्",
            "सबै डाटा हेर्नुहोस्"
        ]
        
        search_option = st.sidebar.radio("खोज विधि छान्नुहोस्:", search_options)
        
        # Search logic
        if search_option == "उन्नत खोज":
            st.subheader("🔍 उन्नत खोज / Advanced Search")
            st.caption("💡 Type in Nepali or English")
            
            with st.form("advanced_search"):
                name_filter = st.text_input("मतदाताको नाम:", "", placeholder="राम or ram")
                parent_filter = st.text_input("पिता/माताको नाम:", "", placeholder="हरि or hari")
                spouse_filter = st.text_input("पति/पत्नीको नाम:", "", placeholder="सीता or sita")
                
                genders = ["सबै"] + list(set([g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)] + ["पुरुष", "महिला"]))
                gender_filter = st.selectbox("लिङ्ग / Gender:", genders, key="adv_gender")
                
                ac1, ac2 = st.columns(2)
                min_age_filter = ac1.number_input("Min Age:", value=0, key="adv_min")
                max_age_filter = ac2.number_input("Max Age:", value=150, key="adv_max")
                
                submit = st.form_submit_button("🔍 खोज्नुहोस् / Search", type="primary", use_container_width=True)
            
            if submit:
                mask = pd.Series([True] * len(df), index=df.index)
                
                # Convert filters to Nepali before searching
                if name_filter:
                    name_nepali = smart_convert_to_nepali(name_filter)
                    mask &= df['मतदाताको नाम_lower'].str.startswith(_normalize_unicode(name_nepali), na=False)
                if parent_filter:
                    parent_nepali = smart_convert_to_nepali(parent_filter)
                    mask &= df['पिता/माताको नाम_lower'].str.startswith(_normalize_unicode(parent_nepali), na=False)
                if spouse_filter:
                    spouse_nepali = smart_convert_to_nepali(spouse_filter)
                    mask &= (df['पति/पत्नीको नाम'] != '-') & df['पति/पत्नीको नाम_lower'].str.startswith(_normalize_unicode(spouse_nepali), na=False)
                if gender_filter != "सबै":
                    mask &= (df['लिङ्ग'] == gender_filter)
                
                age_ok = df['उमेर(वर्ष)'].notna()
                age_in_range = (df['उमेर(वर्ष)'] >= min_age_filter) & (df['उमेर(वर्ष)'] <= max_age_filter)
                mask &= age_ok & age_in_range
                
                filtered_df = df[mask]
                st.markdown("---")
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("⚠️ कुनै पनि मतदाता भेटिएन")
        
        elif search_option == "सबै डाटा हेर्नुहोस्":
            st.subheader("📜 सम्पूर्ण मतदाता सूची")
            st.info(f"📊 कुल मतदाता संख्या: {len(df):,}")
            display_results(df, display_columns)
        
        elif search_option == "मतदाताको नामबाट खोज्नुहोस्":
            st.subheader("👤 मतदाताको नामबाट खोज्नुहोस्")
            st.caption("💡 Type in Nepali or English")
            
            search_name = st.text_input(
                "मतदाताको नाम लेख्नुहोस् / Enter voter name:", 
                "", 
                key="name_search",
                placeholder="राम or ram"
            )
            
            if search_name:
                converted = smart_convert_to_nepali(search_name)
                show_conversion_indicator(search_name, converted)
                
                filtered_df = unicode_prefix_search(df, 'मतदाताको नाम', search_name)
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("⚠️ कुनै पनि मतदाता भेटिएन")
        
        elif search_option == "मतदाता नंबरबाट खोज्नुहोस्":
            st.subheader("🔢 मतदाता नंबरबाट खोज्नुहोस्")
            search_number = st.text_input("मतदाता नंबर लेख्नुहोस्:", "")
            if search_number:
                try:
                    filtered_df = df[df['मतदाता नं'] == int(search_number)]
                    if not filtered_df.empty:
                        st.success("✅ मतदाता भेटियो")
                        display_results(filtered_df, display_columns)
                    else:
                        st.warning("⚠️ कुनै पनि मतदाता भेटिएन")
                except ValueError:
                    st.error("❌ Invalid number format")
        
        elif search_option == "पिता/माताको नामबाट खोज्नुहोस्":
            st.subheader("👨‍👩‍👦 पिता/माताको नामबाट खोज्नुहोस्")
            st.caption("💡 Type in Nepali or English")
            search_parent = st.text_input(
                "पिता वा माताको नाम:", 
                "", 
                key="parent_search",
                placeholder="हरि or hari"
            )
            if search_parent:
                show_conversion_indicator(search_parent, smart_convert_to_nepali(search_parent))
                filtered_df = unicode_prefix_search(df, 'पिता/माताको नाम', search_parent)
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("⚠️ भेटिएन")
        
        elif search_option == "पति/पत्नीको नामबाट खोज्नुहोस्":
            st.subheader("💑 पति/पत्नीको नामबाट खोज्नुहोस्")
            st.caption("💡 Type in Nepali or English")
            search_spouse = st.text_input(
                "पति वा पत्नीको नाम:", 
                "", 
                key="spouse_search",
                placeholder="सीता or sita"
            )
            if search_spouse:
                show_conversion_indicator(search_spouse, smart_convert_to_nepali(search_spouse))
                filtered_df = unicode_prefix_search(df, 'पति/पत्नीको नाम', search_spouse)
                filtered_df = filtered_df[filtered_df['पति/पत्नीको नाम'] != '-']
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("⚠️ भेटिएन")
        
        elif search_option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("⚧️ लिङ्गबाट फिल्टर गर्नुहोस्")
            unique_genders = [g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)]
            gender_options = ["सबै"] + list(set(unique_genders + ["पुरुष", "महिला"]))
            selected_gender = st.selectbox("लिङ्ग छान्नुहोस्:", gender_options)
            
            if selected_gender == "सबै":
                filtered_df = df
            else:
                filtered_df = df[df['लिङ्ग'] == selected_gender]
            
            st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
            display_results(filtered_df, display_columns)
        
        elif search_option == "उमेर दायराबाट खोज्नुहोस्":
            st.subheader("📅 उमेर दायराबाट खोज्नुहोस्")
            c1, c2 = st.columns(2)
            min_age = c1.number_input("न्यूनतम उमेर:", value=18)
            max_age = c2.number_input("अधिकतम उमेर:", value=100)
            
            age_ok = df['उमेर(वर्ष)'].notna()
            in_range = (df['उमेर(वर्ष)'] >= min_age) & (df['उमेर(वर्ष)'] <= max_age)
            filtered_df = df[age_ok & in_range]
            
            st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
            display_results(filtered_df, display_columns)
        
        # Sidebar statistics
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 तथ्याङ्क / Statistics")
        st.sidebar.metric("कुल मतदाता / Total", f"{len(df):,}")
        
        if 'उमेर(वर्ष)' in df.columns:
            genz_voters = df[(df['उमेर(वर्ष)'] >= 18) & (df['उमेर(वर्ष)'] <= 29)]
            st.sidebar.metric("👥 युवा (18-29)", f"{len(genz_voters):,}")
        
        if 'लिङ्ग' in df.columns:
            st.sidebar.write("**लिङ्ग अनुसार:**")
            gender_counts = df['लिङ्ग'].value_counts()
            for gender, count in gender_counts.items():
                percentage = (count / len(df) * 100)
                st.sidebar.write(f"• {gender}: {count:,} ({percentage:.1f}%)")
        
        if 'उमेर(वर्ष)' in df.columns:
            avg_age = df['उमेर(वर्ष)'].dropna().mean()
            st.sidebar.metric("औसत उमेर / Avg Age", f"{avg_age:.1f} वर्ष" if not pd.isna(avg_age) else "—")
    
    except Exception as e:
        logger.exception("App error")
        st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    st.caption("© 2026 Voter List Search System • 🖨️ Screenshot Printing Enabled")


# ============================================================================
# APP ENTRY POINT
# ============================================================================

if not st.session_state.logged_in:
    login_page()
else:
    main_app()