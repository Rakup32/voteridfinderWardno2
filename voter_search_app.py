"""
Voter Search Application - FINAL VERSION WITH ROMAN SUPPORT
===========================================================
Complete integration with Roman to Nepali conversion.

Features:
- ✅ Search in English or Nepali
- ✅ Uses indic-transliteration + custom converter
- ✅ Voter database for exact matches
- ✅ Nepali post-processing
- ✅ Original search logic UNCHANGED
- ✅ Fast with Streamlit caching
- ✅ Production-ready

Author: Voter Search System
Date: 2026-01-31
"""
import os
import sys
import logging
import warnings

# Fix file watcher error
os.environ.setdefault('STREAMLIT_SERVER_FILE_WATCHER_TYPE', 'none')
warnings.filterwarnings('ignore')
logging.getLogger('watchdog').setLevel(logging.ERROR)
logging.getLogger('tornado').setLevel(logging.ERROR)

# Fix WebSocket error
class StderrFilter:
    def __init__(self, original):
        self.original = original
        self.ignore = ['WebSocketClosedError', 'inotify', 'watchdog']
    def write(self, text):
        if not any(p in text for p in self.ignore):
            self.original.write(text)
    def flush(self):
        if hasattr(self.original, 'flush'):
            self.original.flush()

if sys.stderr:
    sys.stderr = StderrFilter(sys.stderr)


import unicodedata
import pandas as pd
import streamlit as st
import base64
import time
import extra_streamlit_components as stx
from credentials import USERNAME, PASSWORD
from print_logic import format_voter_receipt, format_voter_receipt_html


# ============================================================================
# IMPORT NEPALI CONVERTER
# ============================================================================

from nepali_converter import smart_convert_to_nepali, is_devanagari, is_roman, check_installation

def _normalize_unicode(s):
    """Normalize to NFC for consistent Unicode-aware Nepali character comparison."""
    if not isinstance(s, str) or not s:
        return s
    return unicodedata.normalize("NFC", s.strip().lower())


def print_receipt_qz(printer_name, html_content):
    """
    Print voter receipt using QZ Tray with pixel/HTML rendering.
    This function injects JavaScript that connects to QZ Tray and sends HTML to the printer.
    
    Parameters:
    -----------
    printer_name : str
        Name of the thermal printer (e.g., 'zkteco')
    html_content : str
        HTML string to print (from format_voter_receipt_html)
    """
    import html as html_module
    
    # Escape the HTML content for JavaScript
    escaped_html = html_module.escape(html_content).replace('\n', '\\n').replace("'", "\\'")
    
    # JavaScript code to connect to QZ Tray and print
    qz_print_js = f"""
    <script src="https://cdn.jsdelivr.net/npm/qz-tray@2.2/qz-tray.min.js"></script>
    <script>
        (function() {{
            console.log('🖨️ QZ Tray Print Script Loaded');
            
            // Configuration
            const PRINTER_NAME = "{printer_name}";
            const HTML_CONTENT = `{escaped_html}`;
            
            // Connect to QZ Tray
            function connectQZ() {{
                return new Promise((resolve, reject) => {{
                    if (qz.websocket.isActive()) {{
                        console.log('✅ QZ Tray already connected');
                        resolve();
                    }} else {{
                        console.log('🔌 Connecting to QZ Tray...');
                        qz.websocket.connect()
                            .then(() => {{
                                console.log('✅ QZ Tray connected successfully');
                                resolve();
                            }})
                            .catch((err) => {{
                                console.error('❌ QZ Tray connection failed:', err);
                                reject(err);
                            }});
                    }}
                }});
            }}
            
            // Find printer
            function findPrinter() {{
                return new Promise((resolve, reject) => {{
                    qz.printers.find(PRINTER_NAME)
                        .then((found) => {{
                            console.log('✅ Printer found:', found);
                            resolve(found);
                        }})
                        .catch((err) => {{
                            console.error('❌ Printer not found:', err);
                            reject(err);
                        }});
                }});
            }}
            
            // Print using pixel/HTML mode
            function printHTML(printerName) {{
                return new Promise((resolve, reject) => {{
                    // Configure print data for pixel/HTML rendering
                    const config = qz.configs.create(printerName);
                    
                    const data = [{{
                        type: 'pixel',
                        format: 'html',
                        flavor: 'plain',
                        data: HTML_CONTENT
                    }}];
                    
                    console.log('🖨️ Sending print job to:', printerName);
                    
                    qz.print(config, data)
                        .then(() => {{
                            console.log('✅ Print job sent successfully');
                            resolve();
                        }})
                        .catch((err) => {{
                            console.error('❌ Print job failed:', err);
                            reject(err);
                        }});
                }});
            }}
            
            // Main execution
            async function executePrint() {{
                try {{
                    // Step 1: Connect to QZ Tray
                    await connectQZ();
                    
                    // Step 2: Find printer
                    const printer = await findPrinter();
                    
                    // Step 3: Print
                    await printHTML(printer);
                    
                    // Step 4: Show success message to user
                    console.log('✅ Print completed successfully!');
                    
                    // Send success message to Streamlit
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        data: {{status: 'success', message: 'Print job sent successfully'}}
                    }}, '*');
                    
                }} catch (error) {{
                    console.error('❌ Print process failed:', error);
                    
                    // Send error message to Streamlit
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        data: {{status: 'error', message: error.message || 'Print failed'}}
                    }}, '*');
                }}
            }}
            
            // Execute when DOM is ready
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', executePrint);
            }} else {{
                executePrint();
            }}
        }})();
    </script>
    <div style="padding: 20px; text-align: center; font-family: Arial, sans-serif;">
        <h3 style="color: #2c5aa0;">🖨️ Printing...</h3>
        <p>Connecting to QZ Tray and sending print job to <strong>{printer_name}</strong></p>
        <div style="margin-top: 20px;">
            <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #2c5aa0; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
        <style>
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
        <p style="margin-top: 20px; font-size: 14px; color: #666;">
            Check console for status messages
        </p>
    </div>
    """
    
    # Display the component (will execute the print)
    st.components.v1.html(qz_print_js, height=200, scrolling=False)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="मतदाता सूची खोज प्रणाली",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- COOKIE MANAGER SETUP ---
cookie_manager = stx.CookieManager()

# Function to convert image to base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError) as e:
        logger.debug("Image not loaded: %s - %s", image_path, e)
        return None

bell_image_base64 = get_base64_image("bell.png")

# Enhanced Custom CSS
st.markdown("""
    <style>
    .main { padding: 0.75rem 1rem; max-width: 100%; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    h1 { color: #c53030; text-align: center; padding: 0.75rem 0; word-break: break-word; }
    h2, h3 { word-break: break-word; }
    .stTextInput input, .stNumberInput input { min-height: 44px !important; font-size: 16px !important; }
    .stButton > button { min-height: 44px !important; padding: 0.5rem 1rem !important; font-size: 1rem !important; }
    .stSelectbox > div { min-height: 44px !important; }
    [data-testid="stSidebar"] { min-width: 260px; }
    
    /* Conversion indicator */
    .conversion-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    /* Login Page Styling */
    .login-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1rem 1rem 0.5rem; }
    .login-card { width: 100%; max-width: 560px; padding: 2rem 1.75rem 0; text-align: center; margin: 0 auto; display: flex; flex-direction: column; align-items: center; }
    .login-logo { width: 80px; height: 80px; margin: 0 auto 1rem; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.12); background: #f7fafc; animation: login-swing 2s ease-in-out infinite; }
    .login-logo img { width: 100%; height: 100%; object-fit: contain; }
    @keyframes login-swing { 0%, 100% { transform: rotate(0deg); } 25% { transform: rotate(8deg); } 75% { transform: rotate(-8deg); } }
    .login-badge { display: block; font-size: 0.7rem; color: #718096; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem; text-align: center; }
    .login-title { color: #2d3748; font-size: 1.25rem; font-weight: 700; margin-bottom: 0.3rem; line-height: 1.3; text-align: center; }
    .login-subtitle { color: #c53030; font-size: 1rem; font-weight: 600; margin-bottom: 0.2rem; text-align: center; }
    .login-subtitle-en { color: #718096; font-size: 0.9rem; margin-bottom: 0.5rem; text-align: center; }
    .login-divider { height: 1px; background: linear-gradient(90deg, transparent, #e2e8f0, transparent); margin: 0.5rem auto 0.25rem; max-width: 400px; width: 100%; }
    .login-footer { margin-top: 1.5rem; font-size: 0.75rem; color: #a0aec0; text-align: center; }
    .main .block-container > div:has(.login-wrapper) { margin-bottom: 0 !important; }
    .main [data-testid="stForm"] { max-width: 400px; margin-left: auto !important; margin-right: auto !important; }
    
    /* Print Info Box */
    .print-info-box { 
        background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%); 
        border-left: 4px solid #38b2ac; 
        padding: 1.25rem; 
        margin: 1rem 0; 
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(56, 178, 172, 0.15);
    }
    .print-info-box strong { color: #234e52; font-size: 1.1rem; }
    
    /* Voter Card */
    .voter-card { 
        background: #f7fafc; 
        border: 1px solid #e2e8f0; 
        padding: 1rem; 
        margin: 0.75rem 0; 
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .voter-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Success Message Enhancement */
    .stSuccess { 
        border-radius: 8px;
        border-left: 4px solid #38a169;
    }
    
    @media screen and (max-width: 768px) { 
        .main { padding: 0.5rem 0.75rem; } 
        h1 { font-size: 1.35rem !important; }
        .print-info-box { padding: 1rem; }
    }
    @media screen and (max-width: 480px) { 
        .main { padding: 0.4rem 0.5rem; } 
        h1 { font-size: 1.2rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC WITH COOKIES AND SESSION TIMEOUT ---
time.sleep(0.1) 
cookies = cookie_manager.get_all()

# Session timeout: 60 minutes
SESSION_TIMEOUT = 60 * 60  # 60 minutes in seconds

if 'voter_auth' in cookies and cookies['voter_auth'] == 'true':
    # Check if session has timed out
    if 'login_time' not in st.session_state:
        st.session_state.login_time = time.time()
        st.session_state.logged_in = True
    else:
        elapsed_time = time.time() - st.session_state.login_time
        if elapsed_time > SESSION_TIMEOUT:
            # Session expired
            st.session_state.logged_in = False
            st.session_state.pop('login_time', None)
            cookie_manager.delete('voter_auth')
        else:
            st.session_state.logged_in = True
elif 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_login(username, password):
    if not USERNAME and not PASSWORD:
        return False
    return username == USERNAME and password == PASSWORD

def login_page():
    logo_html = (
        f'<div class="login-logo"><img src="data:image/png;base64,{bell_image_base64}" alt="" /></div>'
        if bell_image_base64
        else '<div class="login-logo" style="display:flex;align-items:center;justify-content:center;font-size:2rem;">🗳️</div>'
    )
    header_html = f"""
    <div class="login-wrapper">
    <div class="login-card">
    <div class="login-header-wrap">
        {logo_html}
        <span class="login-badge">Secure access</span>
        <div class="login-title">सुरक्षित प्रवेश</div>
        <div class="login-subtitle">मतदाता सूची खोज प्रणाली</div>
        <div class="login-subtitle-en">Voter List Search System</div>
    </div>
    <div class="login-divider"></div>
    </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("प्रयोगकर्ता नाम / Username", key="username", placeholder="Username")
        password = st.text_input("पासवर्ड / Password", type="password", key="password", placeholder="••••••••")
        submit = st.form_submit_button("लगइन गर्नुहोस् / Login", use_container_width=True)

        if submit:
            if not USERNAME and not PASSWORD:
                st.error("⚠️ Setup credentials in .env file or Streamlit secrets")
            elif check_login(username, password):
                st.session_state.logged_in = True
                st.session_state.login_time = time.time()  # Set login time
                cookie_manager.set('voter_auth', 'true', expires_at=None, key="set_auth")
                st.success("✅ लगइन सफल भयो! (Login Success)")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ गलत प्रयोगकर्ता नाम वा पासवर्ड।")

    st.markdown('<div class="login-footer">🔒 Official use only • Authorized personnel</div>', unsafe_allow_html=True)

def logout():
    st.session_state.logged_in = False
    st.session_state.pop('login_time', None)  # Clear login time
    cookie_manager.delete('voter_auth', key="del_auth")
    time.sleep(0.5)
    st.rerun()

# We keep standard columns to preserve order
STANDARD_COLUMNS = [
    'सि.नं.', 'मतदाता नं', 'मतदाताको नाम', 'उमेर(वर्ष)', 'लिङ्ग',
    'पति/पत्नीको नाम', 'पिता/माताको नाम'
]

@st.cache_data
def load_data():
    df = pd.read_excel('voterlist.xlsx')
    try:
        df.columns = df.columns.str.strip()
    except AttributeError:
        df.columns = [str(c).strip() for c in df.columns]

    if 'उमेर(वर्ष)' in df.columns:
        df['उमेर(वर्ष)'] = pd.to_numeric(df['उमेर(वर्ष)'], errors='coerce')

    # Create helper columns for search
    if 'मतदाताको नाम' in df.columns:
        df['मतदाताको नाम_lower'] = df['मतदाताको नाम'].astype(str).map(lambda s: _normalize_unicode(s))
    if 'पिता/माताको नाम' in df.columns:
        df['पिता/माताको नाम_lower'] = df['पिता/माताको नाम'].astype(str).map(lambda s: _normalize_unicode(s))
    if 'पति/पत्नीको नाम' in df.columns:
        df['पति/पत्नीको नाम_lower'] = df['पति/पत्नीको नाम'].astype(str).map(lambda s: _normalize_unicode(s))
        df['पति/पत्नीको नाम'] = df['पति/पत्नीको नाम'].fillna('-')
        df['पति/पत्नीको नाम_lower'] = df['पति/पत्नीको नाम_lower'].fillna('-')

    return df

def get_display_columns(df):
    """Returns ALL columns from Excel, excluding helper columns."""
    final_cols = [c for c in STANDARD_COLUMNS if c in df.columns]
    
    for c in df.columns:
        if c not in STANDARD_COLUMNS and not c.endswith('_lower') and c not in final_cols and c != 'मतदाता विवरणहरू':
            final_cols.append(c)
            
    return final_cols

def unicode_prefix_search(df, column, search_term):
    """
    Enhanced search with Roman → Nepali conversion support.
    
    THIS IS THE KEY INTEGRATION POINT:
    - Converts Roman input to Nepali BEFORE searching
    - Does NOT modify the search algorithm
    - Does NOT modify the voter data
    """
    if not search_term or column not in df.columns:
        return df
    
    # ============================================
    # ROMAN → NEPALI CONVERSION (NEW!)
    # ============================================
    search_term_nepali = smart_convert_to_nepali(search_term)
    # ============================================
    
    # Original search logic (UNCHANGED)
    normalized = _normalize_unicode(search_term_nepali)
    
    if not normalized:
        return df
    
    lower_col = column + "_lower"
    if lower_col not in df.columns:
        return df
        
    mask = df[lower_col].str.startswith(normalized, na=False)
    return df[mask]

def show_conversion_indicator(original_input: str, converted_input: str):
    """Show visual indicator when conversion happens"""
    if original_input and converted_input != original_input and not is_devanagari(original_input):
        st.markdown(
            f'<div class="conversion-badge">🔄 Searching for: {converted_input}</div>',
            unsafe_allow_html=True
        )

def _build_direct_download_button(receipt_text, voter_num, voter_name):
    """Simple button that directly downloads TXT for thermal printer."""
    import json
    receipt_js = json.dumps(receipt_text)
    voter_num_js = json.dumps(str(voter_num))

    return f"""
<div style="width:100%;">
<button onclick="dlTXT()" style="
    width:100%;padding:16px 10px;border:none;border-radius:10px;cursor:pointer;
    background:linear-gradient(135deg,#38b2ac 0%,#319795 100%);
    color:#fff;font-size:16px;font-weight:600;line-height:1.5;
    transition:all .3s ease;box-shadow: 0 4px 15px rgba(56, 178, 172, 0.3);
  " onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 8px 20px rgba(56,178,172,.5)'"
  onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 4px 15px rgba(56,178,172,.3)'">
  💾 थर्मल प्रिन्टरको लागि डाउनलोड गर्नुहोस्<br>
  <span style="font-size:14px;opacity:.9;font-weight:500">(Download TXT for Thermal Printer)</span>
</button>

<div id="successMsg_{voter_num}" style="
    display:none;
    background:linear-gradient(135deg,#48bb78 0%,#38a169 100%);
    color:white;padding:12px;border-radius:8px;margin-top:10px;
    text-align:center;font-weight:600;font-size:14px;
    animation:successFade .3s ease;">
    ✅ डाउनलोड सफल भयो! (Download Successful!)
</div>

<script>
(function(){{
  var receiptText = {receipt_js};
  var voterNum = {voter_num_js};
  var successMsg = document.getElementById('successMsg_' + voterNum);

  window.dlTXT = function() {{
    var b = new Blob([receiptText],{{type:'text/plain;charset=utf-8'}});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(b);
    a.download = 'voter_' + voterNum + '_thermal.txt';
    a.click();
    
    successMsg.style.display = 'block';
    setTimeout(function() {{
      successMsg.style.display = 'none';
    }}, 3000);
  }}
}})();
</script>

<style>
  @keyframes successFade {{
    from {{ opacity:0; transform:scale(0.95); }}
    to {{ opacity:1; transform:scale(1); }}
  }}
</style>
</div>
"""

def create_qz_print_button_image(voter_num, html_content):
    """
    Create print button using QZ Tray PIXEL mode with HTML rendering.
    Optimized for 80mm thermal printers with Nepali (Devanagari) text.
    
    Parameters:
    -----------
    voter_num : int/str
        Voter number for identification
    html_content : str
        HTML content from format_voter_receipt_html() function
    """
    import json
    
    # Escape HTML content for JavaScript (simple and safe)
    html_escaped = (html_content
                   .replace('\\', '\\\\')
                   .replace('`', '\\`')
                   .replace('$', '\\$'))
    
    html = f"""
    <div style="width: 100%; padding: 8px;">
        <!-- Print Button -->
        <button id="printBtn_{voter_num}" onclick="printReceipt_{voter_num}()" style="
            width: 100%;
            padding: 14px 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            margin-bottom: 10px;
        " onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 20px rgba(102,126,234,.5)'"
           onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 4px 15px rgba(102,126,234,.3)'">
            🖨️ Print Slip<br>
            <span style="font-size: 12px; opacity: 0.9; font-weight: 500;">(Thermal Printer)</span>
        </button>
        
        <!-- Status Display -->
        <div id="status_{voter_num}" style="
            padding: 10px;
            border-radius: 6px;
            font-size: 12px;
            line-height: 1.4;
            display: none;
            margin-top: 8px;
        "></div>
    </div>
    
    <!-- QZ Tray Library -->
    <script src="https://cdn.jsdelivr.net/npm/qz-tray@2.2/qz-tray.min.js"></script>
    
    <script>
    (function() {{
        // HTML content for printing
        const htmlContent = `{html_escaped}`;
        
        const statusDiv = document.getElementById('status_{voter_num}');
        const printBtn = document.getElementById('printBtn_{voter_num}');
        
        function updateStatus(message, type = 'info') {{
            const colors = {{
                'info': '#3182ce',
                'success': '#38a169',
                'error': '#e53e3e',
                'warning': '#d69e2e'
            }};
            statusDiv.style.display = 'block';
            statusDiv.style.background = colors[type] + '22';
            statusDiv.style.border = '2px solid ' + colors[type];
            statusDiv.style.color = colors[type];
            statusDiv.innerHTML = message;
        }}
        
        window.printReceipt_{voter_num} = async function() {{
            try {{
                // Disable button
                printBtn.disabled = true;
                printBtn.style.opacity = '0.6';
                printBtn.style.cursor = 'not-allowed';
                
                // Step 1: Connect to QZ Tray
                updateStatus('🔌 Connecting to QZ Tray...', 'info');
                
                if (!qz.websocket.isActive()) {{
                    await qz.websocket.connect();
                }}
                
                updateStatus('✅ Connected to QZ Tray', 'success');
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Step 2: Find printer
                updateStatus('🔍 Finding printer...', 'info');
                
                const printers = await qz.printers.find();
                console.log('Available printers:', printers);
                
                // Look for 'zkteco' printer first
                let targetPrinter = printers.find(p => 
                    p.toLowerCase().includes('zkteco')
                );
                
                // If not found, use the first available printer
                if (!targetPrinter) {{
                    targetPrinter = printers[0];
                    updateStatus(`⚠️ Using: ${{targetPrinter}}`, 'warning');
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }} else {{
                    updateStatus(`✅ Found: ${{targetPrinter}}`, 'success');
                    await new Promise(resolve => setTimeout(resolve, 500));
                }}
                
                // Step 3: Configure printer
                const config = qz.configs.create(targetPrinter);
                
                // Step 4: Prepare print data using PIXEL mode with HTML
                const printData = [{{
                    type: 'pixel',
                    format: 'html',
                    flavor: 'plain',
                    data: htmlContent
                }}];
                
                // Step 5: Send to printer
                updateStatus('🖨️ Printing...', 'info');
                
                await qz.print(config, printData);
                
                // Success
                updateStatus('✅ Print successful! / मुद्रण सफल!', 'success');
                
                // Reset after 3 seconds
                setTimeout(() => {{
                    printBtn.disabled = false;
                    printBtn.style.opacity = '1';
                    printBtn.style.cursor = 'pointer';
                    statusDiv.style.display = 'none';
                }}, 3000);
                
            }} catch (err) {{
                console.error('Print Error:', err);
                
                // User-friendly error messages
                let message = '❌ Error: ';
                if (err.message && err.message.includes('establish')) {{
                    message += 'QZ Tray is not running! Please start QZ Tray application.';
                }} else if (err.message && err.message.includes('find')) {{
                    message += 'Printer not found! Please check if printer is ON and connected.';
                }} else {{
                    message += err.message || 'Unknown error occurred';
                }}
                
                updateStatus(message + '<br><small>Check console (F12) for details</small>', 'error');
                
                // Re-enable button
                printBtn.disabled = false;
                printBtn.style.opacity = '1';
                printBtn.style.cursor = 'pointer';
            }}
        }};
    }})();
    </script>
    """
    
    return html


def create_qz_print_button_text(voter_num, voter_name, age, gender, parent, spouse):
    """
    Create print button using ESC/POS commands with proper encoding for Nepali text.
    Uses codepage switching for Nepali Unicode support.
    
    Parameters:
    -----------
    voter_num : int/str
    voter_name : str
    age : int/str
    gender : str
    parent : str
    spouse : str
    """
    import json
    import base64
    
    # Create the receipt text
    voter_name_str = str(voter_name)
    parent_str = str(parent)
    spouse_str = str(spouse) if spouse and spouse != '-' else ''
    
    # Encode to UTF-8 bytes, then to base64 for safe transmission
    receipt_lines = [
        "",
        "==========================================",
        "         मतदाता विवरण",
        "        VOTER DETAILS",
        "==========================================",
        "",
        f"मतदाता नं: {voter_num}",
        "",
        f"नाम: {voter_name_str}",
        f"उमेर: {age} वर्ष | लिङ्ग: {gender}",
        f"पिता/माता: {parent_str}",
    ]
    
    if spouse_str:
        receipt_lines.append(f"पति/पत्नी: {spouse_str}")
    
    receipt_lines.extend([
        "",
        "",
        "         _________________",
        "         दस्तखत / Signature",
        "",
        "------------------------------------------",
        "        धन्यवाद / Thank You",
        "==========================================",
        "",
        "",
        ""
    ])
    
    receipt_text = "\n".join(receipt_lines)
    
    # Encode to base64 for safe transmission
    receipt_bytes = receipt_text.encode('utf-8')
    receipt_base64 = base64.b64encode(receipt_bytes).decode('ascii')
    
    html = f"""
    <div style="width: 100%; padding: 8px;">
        <button id="printBtn_{voter_num}" onclick="printReceipt_{voter_num}()" style="
            width: 100%;
            padding: 14px 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            margin-bottom: 10px;
        " onmouseover="this.style.transform='translateY(-2px)'"
           onmouseout="this.style.transform='translateY(0)'">
            🖨️ Print Slip
        </button>
        
        <div id="status_{voter_num}" style="
            padding: 10px;
            border-radius: 6px;
            font-size: 12px;
            line-height: 1.4;
            display: none;
            margin-top: 8px;
        "></div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/qz-tray@2.2.3/qz-tray.min.js"></script>
    
    <script>
    (function() {{
        const receiptBase64 = "{receipt_base64}";
        const statusDiv = document.getElementById('status_{voter_num}');
        const printBtn = document.getElementById('printBtn_{voter_num}');
        
        function updateStatus(msg, type) {{
            const colors = {{'info':'#3182ce','success':'#38a169','error':'#e53e3e','warning':'#d69e2e'}};
            statusDiv.style.display = 'block';
            statusDiv.style.background = colors[type] + '22';
            statusDiv.style.border = '2px solid ' + colors[type];
            statusDiv.style.color = colors[type];
            statusDiv.innerHTML = msg;
        }}
        
        window.printReceipt_{voter_num} = async function() {{
            try {{
                printBtn.disabled = true;
                printBtn.style.opacity = '0.6';
                
                updateStatus('🔌 Connecting...', 'info');
                
                if (!qz.websocket.isActive()) {{
                    await qz.websocket.connect();
                }}
                
                updateStatus('✅ Connected', 'success');
                
                const printers = await qz.printers.find();
                let printer = printers.find(p => p.toLowerCase().includes('zkteco')) || printers[0];
                
                updateStatus('🖨️ Preparing...', 'info');
                
                // Decode base64 to get UTF-8 text
                const receiptText = decodeURIComponent(escape(atob(receiptBase64)));
                
                const config = qz.configs.create(printer, {{
                    encoding: 'UTF-8',
                    colorType: 'blackwhite'
                }});
                
                // ESC/POS commands for UTF-8 support
                const initCmd = '\\x1B\\x40';  // Initialize printer
                const utf8Cmd = '\\x1B\\x74\\x10';  // Select UTF-8 character set
                const cutCmd = '\\x1D\\x56\\x00';  // Full cut
                
                const printData = [
                    {{
                        type: 'raw',
                        format: 'command',
                        data: initCmd
                    }},
                    {{
                        type: 'raw',
                        format: 'command',
                        data: utf8Cmd
                    }},
                    {{
                        type: 'raw',
                        format: 'plain',
                        data: receiptText,
                        options: {{ encoding: 'UTF-8' }}
                    }},
                    {{
                        type: 'raw',
                        format: 'command',
                        data: cutCmd
                    }}
                ];
                
                updateStatus('🖨️ Printing...', 'info');
                await qz.print(config, printData);
                
                updateStatus('✅ सफल!', 'success');
                
                setTimeout(() => {{
                    printBtn.disabled = false;
                    printBtn.style.opacity = '1';
                    statusDiv.style.display = 'none';
                }}, 3000);
                
            }} catch (err) {{
                console.error(err);
                let msg = '❌ Error: ';
                if (err.message.includes('establish')) msg += 'Start QZ Tray!';
                else if (err.message.includes('find')) msg += 'Turn ON printer';
                else msg += err.message + '<br>Check console (F12)';
                updateStatus(msg, 'error');
                printBtn.disabled = false;
                printBtn.style.opacity = '1';
            }}
        }};
    }})();
    </script>
    """
    
    return html


def create_qz_print_button(voter_num, html_content, voter_name):
    """
    Create an HTML button with embedded QZ Tray printing functionality.
    Uses PLAIN TEXT mode instead of HTML for maximum compatibility.
    
    Parameters:
    -----------
    voter_num : int/str
        Voter number for identification
    html_content : str
        HTML content (will be ignored, we'll use plain text)
    voter_name : str
        Voter name for display
    
    Returns:
    --------
    str : Complete HTML with button and QZ Tray printing logic
    """
    import json
    
    # Instead of HTML, we'll send the plain text version
    # This is much more reliable for thermal printers
    from print_logic import format_voter_receipt
    
    # Get the voter data to create plain text receipt
    # Note: voter_name is actually the full voter dict passed as parameter
    
    html = f"""
    <div style="width: 100%; padding: 8px;">
        <!-- Print Button -->
        <button id="printBtn_{voter_num}" onclick="printReceipt_{voter_num}()" style="
            width: 100%;
            padding: 14px 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            margin-bottom: 10px;
        " onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 20px rgba(102,126,234,.5)'"
           onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 4px 15px rgba(102,126,234,.3)'">
            🖨️ Print Slip<br>
            <span style="font-size: 12px; opacity: 0.9; font-weight: 500;">(Direct Thermal Print)</span>
        </button>
        
        <!-- Status Display -->
        <div id="status_{voter_num}" style="
            padding: 10px;
            border-radius: 6px;
            font-size: 12px;
            line-height: 1.4;
            display: none;
            margin-top: 8px;
        "></div>
        
        <!-- Hidden data -->
        <div id="voterData_{voter_num}" style="display:none;"></div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/qz-tray@2.2.3/qz-tray.min.js"></script>
    
    <script>
    (function() {{
        const statusDiv = document.getElementById('status_{voter_num}');
        const printBtn = document.getElementById('printBtn_{voter_num}');
        
        function updateStatus(message, type = 'info') {{
            const colors = {{
                'info': '#3182ce',
                'success': '#38a169',
                'error': '#e53e3e',
                'warning': '#d69e2e'
            }};
            statusDiv.style.display = 'block';
            statusDiv.style.background = colors[type] + '22';
            statusDiv.style.border = '2px solid ' + colors[type];
            statusDiv.style.color = colors[type];
            statusDiv.innerHTML = message;
        }}
        
        window.printReceipt_{voter_num} = async function() {{
            try {{
                printBtn.disabled = true;
                printBtn.style.opacity = '0.6';
                printBtn.style.cursor = 'not-allowed';
                
                updateStatus('🔌 जडान गर्दै...', 'info');
                
                if (!qz.websocket.isActive()) {{
                    await qz.websocket.connect();
                }}
                updateStatus('✅ जडान भयो', 'success');
                
                const printers = await qz.printers.find();
                console.log('Printers:', printers);
                
                let targetPrinter = printers.find(p => 
                    p.toLowerCase().includes('zkteco')
                );
                
                if (!targetPrinter) {{
                    targetPrinter = printers[0];
                    updateStatus(`Using: ${{targetPrinter}}`, 'warning');
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }} else {{
                    updateStatus(`🖨️ ${{targetPrinter}}`, 'success');
                    await new Promise(resolve => setTimeout(resolve, 500));
                }}
                
                const config = qz.configs.create(targetPrinter, {{
                    encoding: 'UTF-8'
                }});
                
                // Create simple text receipt - works better than HTML
                const receipt = `
==========================================
         मतदाता विवरण
        VOTER DETAILS
==========================================

मतदाता नं: {voter_num}

नाम: {voter_name}

------------------------------------------
         धन्यवाद / Thank You
==========================================


`;
                
                // Auto-cut command
                const cutCmd = '\\x1B\\x69';
                
                const printData = [
                    {{
                        type: 'raw',
                        format: 'plain',
                        data: receipt
                    }},
                    {{
                        type: 'raw',
                        format: 'command',
                        data: cutCmd
                    }}
                ];
                
                updateStatus('🖨️ प्रिन्ट गर्दै...', 'info');
                await qz.print(config, printData);
                
                updateStatus('✅ सफल!', 'success');
                
                setTimeout(() => {{
                    printBtn.disabled = false;
                    printBtn.style.opacity = '1';
                    printBtn.style.cursor = 'pointer';
                    statusDiv.style.display = 'none';
                }}, 3000);
                
            }} catch (err) {{
                console.error('Error:', err);
                let msg = '❌ त्रुटि:<br>';
                
                if (err.message && err.message.includes('Unable to establish')) {{
                    msg += '<strong>QZ Tray बन्द छ</strong><br>Start QZ Tray!';
                }} else if (err.message && err.message.includes('Unable to find')) {{
                    msg += '<strong>प्रिन्टर भेटिएन</strong><br>Turn ON printer';
                }} else {{
                    msg += err.message || 'Unknown';
                    msg += '<br>Press F12 for details';
                }}
                
                updateStatus(msg, 'error');
                
                printBtn.disabled = false;
                printBtn.style.opacity = '1';
                printBtn.style.cursor = 'pointer';
            }}
        }};
    }})();
    </script>
    """
    
    return html


def show_results_table_with_print(data, columns):
    """Display results with direct download for thermal printer."""
    if data.empty:
        return

    # Use container with anchor for scrolling
    st.markdown('<div id="results-anchor" style="scroll-margin-top: 20px;"></div>', unsafe_allow_html=True)
    
    # Inject JavaScript to scroll to results
    st.components.v1.html("""
    <script>
    (function() {
        // Multiple attempts to ensure scroll works
        function scrollToResults() {
            // Method 1: Scroll to bottom
            window.parent.scrollTo({
                top: window.parent.document.body.scrollHeight,
                behavior: 'smooth'
            });
            
            // Method 2: Find and scroll to element
            setTimeout(function() {
                const anchor = window.parent.document.getElementById('results-anchor');
                if (anchor) {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        }
        
        // Try immediately
        scrollToResults();
        
        // Try again after a delay
        setTimeout(scrollToResults, 300);
        setTimeout(scrollToResults, 600);
    })();
    </script>
    """, height=0)
    
    st.caption(f"📊 कुल मतदाता: {len(data):,}")

    for idx, row in data.iterrows():
        voter_name = row.get('मतदाताको नाम', 'N/A')
        voter_num = row.get('मतदाता नं', 'N/A')
        age = row.get('उमेर(वर्ष)', 'N/A')
        gender = row.get('लिङ्ग', 'N/A')

        with st.expander(f"🗳️ {voter_name} — नं: {voter_num} | {gender}, {age} वर्ष", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                for col in columns:
                    if col in row.index:
                        value = row[col] if pd.notna(row[col]) else '-'
                        st.text(f"{col}: {value}")

            with col2:
                voter_dict = row.to_dict()
                
                # Generate HTML receipt for image-based printing (most reliable for Nepali)
                html_receipt = format_voter_receipt_html(voter_dict)
                
                # Print Slip button using IMAGE mode (renders HTML as image)
                print_button_html = create_qz_print_button_image(voter_num, html_receipt)
                st.components.v1.html(print_button_html, height=180, scrolling=False)
                
                st.markdown("---")
                
                # Original download button for thermal printer
                receipt_text = format_voter_receipt(voter_dict)
                download_button = _build_direct_download_button(receipt_text, voter_num, voter_name)
                st.components.v1.html(download_button, height=120, scrolling=False)

def show_results_table(data, columns):
    """Standard table display without print buttons."""
    if data.empty:
        return
    calculated_height = (len(data) + 1) * 35 
    display_height = max(150, min(calculated_height, 800))
    st.dataframe(data[columns], use_container_width=True, height=display_height, hide_index=True)

def main_app():
    # Check session timeout
    if 'login_time' in st.session_state:
        elapsed_time = time.time() - st.session_state.login_time
        remaining_time = SESSION_TIMEOUT - elapsed_time
        
        if remaining_time <= 0:
            # Session expired
            st.warning("⏰ सत्र समाप्त भयो! कृपया पुन: लगइन गर्नुहोस् / Session expired! Please login again")
            logout()
            return
        
        # Show remaining time in sidebar
        minutes_left = int(remaining_time / 60)
        if minutes_left < 10:
            st.sidebar.warning(f"⏰ {minutes_left} min left")
    
    st.title("🗳️ मतदाता सूची खोज प्रणाली")
    
    with st.sidebar:
        if st.button("🚪 Logout / बाहिर निस्कनुहोस्", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    try:
        with st.spinner('📂 डाटा लोड गर्दै... / Loading data...'):
            df = load_data()

        display_columns = get_display_columns(df)
        
        if not display_columns:
            st.error("❌ Excel columns missing.")
            return

        # Statistics section at the top
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
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 प्रदर्शन मोड / Display Mode")
        
        display_mode = st.sidebar.radio(
            "मोड छान्नुहोस् / Select Mode:",
            ["🖨️ Print View (थर्मल प्रिन्टर)", "📋 Table View (तालिका)"],
            index=0,
            help="Print View: थर्मल प्रिन्टरको लागि TXT डाउनलोड गर्नुहोस् | Table View: सबै मतदाता एकै पटक हेर्नुहोस्"
        )
        use_print_view = (display_mode == "🖨️ Print View (थर्मल प्रिन्टर)")
        
        st.sidebar.markdown("---")
        
        default_index = 0
        search_option = st.sidebar.selectbox(
            "खोज प्रकार छान्नुहोस्:",
            ["उन्नत खोज (सबै फिल्टर)", "सबै डाटा हेर्नुहोस्", "मतदाताको नामबाट खोज्नुहोस्", "मतदाता नंबरबाट खोज्नुहोस्", 
             "पिता/माताको नामबाट खोज्नुहोस्", "पति/पत्नीको नामबाट खोज्नुहोस्",
             "लिङ्गबाट फिल्टर गर्नुहोस्", "उमेर दायराबाट खोज्नुहोस्"],
            index=default_index
        )
        
        def display_results(filtered_df, display_cols):
            if use_print_view:
                show_results_table_with_print(filtered_df, display_cols)
            else:
                show_results_table(filtered_df, display_cols)
        
        if search_option == "उन्नत खोज (सबै फिल्टर)":
            st.subheader("🔍 उन्नत खोज / Advanced Search")
            st.caption("💡 Type in Nepali or English (राम or ram)")
            
            col1, col2 = st.columns(2)
            with col1:
                name_filter = st.text_input(
                    "मतदाताको नाम / Voter Name:", 
                    key="adv_name",
                    placeholder="राम or ram"
                )
                if name_filter:
                    converted = smart_convert_to_nepali(name_filter)
                    if use_print_view and converted != name_filter:
                        st.info(f"🔍 {converted}")
                    elif not use_print_view:
                        show_conversion_indicator(name_filter, converted)
                
                parent_filter = st.text_input(
                    "पिता/माताको नाम / Parent Name:", 
                    key="adv_parent",
                    placeholder="हरि or hari"
                )
                if parent_filter:
                    converted = smart_convert_to_nepali(parent_filter)
                    if use_print_view and converted != parent_filter:
                        st.info(f"🔍 {converted}")
                    elif not use_print_view:
                        show_conversion_indicator(parent_filter, converted)
                
                spouse_filter = st.text_input(
                    "पति/पत्नीको नाम / Spouse Name:", 
                    key="adv_spouse",
                    placeholder="सीता or sita"
                )
                if spouse_filter:
                    converted = smart_convert_to_nepali(spouse_filter)
                    if use_print_view and converted != spouse_filter:
                        st.info(f"🔍 {converted}")
                    elif not use_print_view:
                        show_conversion_indicator(spouse_filter, converted)
                
            with col2:
                if use_print_view:
                    # In print view, disable gender filter
                    genders = ["सबै"] + list(set([g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)] + ["पुरुष", "महिला"]))
                    gender_filter = st.selectbox("लिङ्ग / Gender:", genders, key="adv_gender", disabled=True)
                else:
                    # In table view, gender filter is enabled
                    genders = ["सबै"] + list(set([g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)] + ["पुरुष", "महिला"]))
                    gender_filter = st.selectbox("लिङ्ग / Gender:", genders, key="adv_gender")
                ac1, ac2 = st.columns(2)
                min_age_filter = ac1.number_input("Min Age:", value=0, key="adv_min")
                max_age_filter = ac2.number_input("Max Age:", value=150, key="adv_max")

            if st.button("🔍 खोज्नुहोस् / Search", type="primary", use_container_width=True):
                # Validation for print view - require at least one search field
                if use_print_view:
                    has_input = any([name_filter, parent_filter, spouse_filter])
                    if not has_input:
                        st.error("⚠️ कृपया खोज्नको लागि कम्तिमा एक फिल्ड भर्नुहोस् / Please fill at least one search field")
                        st.stop()
                
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
                # Only apply gender filter in table view (not disabled)
                if not use_print_view and gender_filter != "सबै":
                    mask &= (df['लिङ्ग'] == gender_filter)
                
                age_ok = df['उमेर(वर्ष)'].notna()
                age_in_range = (df['उमेर(वर्ष)'] >= min_age_filter) & (df['उमेर(वर्ष)'] <= max_age_filter)
                mask &= age_ok & age_in_range
                
                filtered_df = df[mask]
                st.markdown("---")
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("⚠️ कुनै पनि मतदाता भेटिएन")
        
        elif search_option == "सबै डाटा हेर्नुहोस्":
            st.subheader("📜 सम्पूर्ण मतदाता सूची")
            
            if use_print_view:
                st.warning("⚠️ **Print View मा सबै डाटा देखाउन सकिँदैन**")
                st.info("""
                🖨️ **Print View** थर्मल प्रिन्टरको लागि हो।
                
                कृपया:
                - अन्य खोज विकल्पबाट विशेष मतदाता खोज्नुहोस्, वा
                - **Table View** मा स्विच गर्नुहोस् सबै डाटा हेर्न
                """)
                st.info(f"📊 कुल मतदाता संख्या: {len(df):,}")
            else:
                display_results(df, display_columns)
                st.info(f"📊 कुल मतदाता संख्या: {len(df):,}")
        
        elif search_option == "मतदाताको नामबाट खोज्नुहोस्":
            st.subheader("👤 मतदाताको नामबाट खोज्नुहोस्")
            st.caption("💡 Type in Nepali or English")
            with st.expander("📘 Examples"):
                st.markdown("""
                **Nepali:** 'र' finds 'राम', 'रमेश', 'राधा'
                
                **English:** 'r' or 'ram' finds 'राम', 'रमेश'
                """)
            
            search_name = st.text_input(
                "मतदाताको नाम लेख्नुहोस् / Enter voter name:", 
                "", 
                key="name_search",
                placeholder="राम or ram"
            )
            
            if search_name:
                converted = smart_convert_to_nepali(search_name)
                
                # Show live conversion indicator
                if use_print_view and converted != search_name:
                    st.info(f"🔍 Searching for: **{converted}**")
                elif not use_print_view:
                    show_conversion_indicator(search_name, converted)
                
                filtered_df = unicode_prefix_search(df, 'मतदाताको नाम', search_name)
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("⚠️ कुनै पनि मतदाता भेटिएन")
            elif use_print_view:
                st.info("💡 कृपया माथि मतदाताको नाम लेख्नुहोस् / Please enter voter name above")
        
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
            elif use_print_view:
                st.info("💡 कृपया माथि मतदाता नंबर लेख्नुहोस् / Please enter voter number above")

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
                converted = smart_convert_to_nepali(search_parent)
                
                # Show live conversion indicator
                if use_print_view and converted != search_parent:
                    st.info(f"🔍 Searching for: **{converted}**")
                elif not use_print_view:
                    show_conversion_indicator(search_parent, converted)
                
                filtered_df = unicode_prefix_search(df, 'पिता/माताको नाम', search_parent)
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,} भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("⚠️ भेटिएन")
            elif use_print_view:
                st.info("💡 कृपया माथि पिता/माताको नाम लेख्नुहोस् / Please enter parent name above")

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
                converted = smart_convert_to_nepali(search_spouse)
                
                # Show live conversion indicator
                if use_print_view and converted != search_spouse:
                    st.info(f"🔍 Searching for: **{converted}**")
                elif not use_print_view:
                    show_conversion_indicator(search_spouse, converted)
                
                filtered_df = unicode_prefix_search(df, 'पति/पत्नीको नाम', search_spouse)
                filtered_df = filtered_df[filtered_df['पति/पत्नीको नाम'] != '-']
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,} भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("⚠️ भेटिएन")
            elif use_print_view:
                st.info("💡 कृपया माथि पति/पत्नीको नाम लेख्नुहोस् / Please enter spouse name above")

        elif search_option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("⚧️ लिङ्गबाट फिल्टर गर्नुहोस्")
            
            if use_print_view:
                st.warning("⚠️ **Print View मा लिङ्ग फिल्टर उपलब्ध छैन**")
                st.info("""
                🖨️ **Print View** मा लिङ्ग फिल्टर अक्षम गरिएको छ।
                
                कृपया:
                - अन्य खोज विकल्प प्रयोग गर्नुहोस् (नाम, नंबर, आदि), वा
                - **Table View** मा स्विच गर्नुहोस् लिङ्ग फिल्टर प्रयोग गर्न
                """)
            else:
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
            
            if filtered_df.empty:
                st.warning("⚠️ यस उमेर दायरामा कुनै मतदाता भेटिएन")
            else:
                if not use_print_view:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
                display_results(filtered_df, display_columns)

    except FileNotFoundError:
        st.error("❌ voterlist.xlsx not found. Please upload the file.")
    except Exception as e:
        logger.exception("App error")
        st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    st.caption("© 2026 Voter List Search System • 🔄 Roman/English Support Enabled")

if not st.session_state.logged_in:
    login_page()
else:
    main_app()