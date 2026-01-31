import logging
import unicodedata
import pandas as pd
import streamlit as st
import base64
import time
import extra_streamlit_components as stx
from credentials import USERNAME, PASSWORD
from print_logic import format_voter_receipt

def _normalize_unicode(s):
    """Normalize to NFC for consistent Unicode-aware Nepali character comparison."""
    if not isinstance(s, str) or not s:
        return s
    return unicodedata.normalize("NFC", s.strip().lower())

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
# ----------------------------

# Function to convert image to base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError) as e:
        logger.debug("Image not loaded: %s - %s", image_path, e)
        return None

bell_image_base64 = get_base64_image("bell.png")

# Custom CSS with Modal Styles
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
    .print-info-box { background: #e6fffa; border-left: 4px solid #38b2ac; padding: 1rem; margin: 0.5rem 0; border-radius: 4px; }
    
    /* Modal Styles */
    .modal-overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.75);
        z-index: 9999;
        animation: fadeIn 0.3s;
    }
    
    .modal-overlay.active {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .modal-container {
        background: white;
        border-radius: 12px;
        max-width: 600px;
        width: 90%;
        max-height: 90vh;
        overflow: hidden;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        animation: slideIn 0.3s;
    }
    
    .modal-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px 12px 0 0;
    }
    
    .modal-header h2 {
        margin: 0;
        font-size: 1.5rem;
        color: white;
    }
    
    .modal-body {
        padding: 1.5rem;
        max-height: 60vh;
        overflow-y: auto;
    }
    
    .receipt-preview {
        background: #f7fafc;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
        line-height: 1.4;
        margin-bottom: 1.5rem;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .button-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .modal-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem;
        border-radius: 8px;
        cursor: pointer;
        font-size: 0.95rem;
        font-weight: 600;
        transition: all 0.3s;
        text-align: center;
    }
    
    .modal-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    .modal-button.primary {
        background: linear-gradient(135deg, #38b2ac 0%, #319795 100%);
    }
    
    .modal-button.secondary {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
    }
    
    .modal-button.danger {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
    }
    
    .modal-button .icon {
        display: block;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    .modal-button .label {
        display: block;
        font-size: 0.85rem;
        opacity: 0.9;
    }
    
    .close-button {
        width: 100%;
        margin-top: 1rem;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideIn {
        from { 
            opacity: 0;
            transform: translateY(-50px);
        }
        to { 
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @media screen and (max-width: 768px) { 
        .main { padding: 0.5rem 0.75rem; } 
        h1 { font-size: 1.35rem !important; }
        .modal-container { width: 95%; }
        .button-grid { grid-template-columns: 1fr; }
    }
    @media screen and (max-width: 480px) { 
        .main { padding: 0.4rem 0.5rem; } 
        h1 { font-size: 1.2rem !important; } 
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC WITH COOKIES ---
time.sleep(0.1) 
cookies = cookie_manager.get_all()
if 'voter_auth' in cookies and cookies['voter_auth'] == 'true':
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
                st.error("Setup credentials in .env")
            elif check_login(username, password):
                st.session_state.logged_in = True
                cookie_manager.set('voter_auth', 'true', expires_at=None, key="set_auth")
                st.success("लगइन सफल भयो! (Login Success)")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("गलत प्रयोगकर्ता नाम वा पासवर्ड।")

    st.markdown('<div class="login-footer">Official use only • Authorized personnel</div>', unsafe_allow_html=True)

def logout():
    st.session_state.logged_in = False
    cookie_manager.delete('voter_auth', key="del_auth")
    time.sleep(0.5)
    st.rerun()

# --------------------------------

# We keep standard columns to preserve order, but we will add new ones dynamically
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

    # Create helper columns for search (ending in _lower)
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
    """
    Returns ALL columns from the Excel file, excluding internal helper columns.
    """
    final_cols = [c for c in STANDARD_COLUMNS if c in df.columns]
    for c in df.columns:
        if c not in STANDARD_COLUMNS and not c.endswith('_lower') and c not in final_cols:
            final_cols.append(c)
    return final_cols

def unicode_prefix_search(df, column, search_term):
    if not search_term or column not in df.columns:
        return df
    normalized = _normalize_unicode(search_term)
    if not normalized:
        return df
    lower_col = column + "_lower"
    if lower_col not in df.columns:
        return df
    mask = df[lower_col].str.startswith(normalized, na=False)
    return df[mask]

def create_print_modal_html(receipt_text, voter_num):
    """Create HTML for print modal with JavaScript"""
    
    # Escape the receipt text for JavaScript
    receipt_escaped = receipt_text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    
    # Create HTML version of receipt
    receipt_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Courier New', monospace; white-space: pre; padding: 20px; }}
        </style>
    </head>
    <body>{receipt_text}</body>
    </html>
    """
    receipt_html_escaped = receipt_html.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    
    modal_html = f"""
    <div id="printModal" class="modal-overlay">
        <div class="modal-container">
            <div class="modal-header">
                <h2>🖨️ मुद्रण पूर्वावलोकन / Print Preview</h2>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                    मतदाता नं: {voter_num} | 58mm Thermal Printer Format
                </p>
            </div>
            <div class="modal-body">
                <div class="receipt-preview" id="receiptContent">{receipt_text}</div>
                
                <div class="button-grid">
                    <button class="modal-button primary" onclick="printReceipt()">
                        <span class="icon">🖨️</span>
                        <strong>Browser Print</strong>
                        <span class="label">Instant print</span>
                    </button>
                    
                    <button class="modal-button secondary" onclick="downloadTXT()">
                        <span class="icon">💾</span>
                        <strong>Download TXT</strong>
                        <span class="label">For thermal printer</span>
                    </button>
                    
                    <button class="modal-button secondary" onclick="downloadHTML()">
                        <span class="icon">📄</span>
                        <strong>Download HTML</strong>
                        <span class="label">Best format</span>
                    </button>
                </div>
                
                <button class="modal-button danger close-button" onclick="closeModal()">
                    ❌ बन्द गर्नुहोस् (Close)
                </button>
            </div>
        </div>
    </div>
    
    <script>
        const receiptText = '{receipt_escaped}';
        const receiptHTML = '{receipt_html_escaped}';
        const voterNum = '{voter_num}';
        
        function printReceipt() {{
            const printWindow = window.open('', '_blank');
            printWindow.document.write(receiptHTML);
            printWindow.document.close();
            printWindow.focus();
            setTimeout(() => {{
                printWindow.print();
                printWindow.close();
            }}, 250);
        }}
        
        function downloadTXT() {{
            const blob = new Blob([receiptText.replace(/\\\\n/g, '\\n')], {{ type: 'text/plain;charset=utf-8' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'voter_' + voterNum + '.txt';
            link.click();
        }}
        
        function downloadHTML() {{
            const blob = new Blob([receiptHTML.replace(/\\\\n/g, '\\n')], {{ type: 'text/html;charset=utf-8' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'voter_' + voterNum + '.html';
            link.click();
        }}
        
        function closeModal() {{
            document.getElementById('printModal').classList.remove('active');
        }}
        
        // Close on outside click
        document.getElementById('printModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeModal();
            }}
        }});
        
        // Close on Escape key
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
    """
    
    return modal_html

def show_results_table_with_print(data, columns):
    """Display results table with print buttons - NO PAGE RELOAD VERSION"""
    if data.empty:
        return
    
    st.markdown("""
    <div class="print-info-box">
        <strong>🖨️ प्रिन्ट मोड सक्रिय छ / Print Mode Active</strong><br>
        📋 प्रत्येक मतदातामा क्लिक गर्नुहोस् र Print बटन थिच्नुहोस्।<br>
        💡 Print opens in popup - NO page reload!
    </div>
    """, unsafe_allow_html=True)
    
    st.caption(f"📊 कुल मतदाता: {len(data):,}")
    
    for idx, row in data.iterrows():
        voter_name = row.get('मतदाताको नाम', 'N/A')
        voter_num = row.get('मतदाता नं', 'N/A')
        
        with st.expander(f"🗳️ {voter_name} — मतदाता नं: {voter_num}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                for col in columns:
                    if col in row.index and col != 'मतदाता विवरणहरू':
                        value = row[col] if pd.notna(row[col]) else '-'
                        st.text(f"{col}: {value}")
            
            with col2:
                # Create unique button with onclick to open modal
                button_id = f"printBtn_{idx}"
                
                # Generate receipt text
                voter_dict = row.to_dict()
                receipt_text = format_voter_receipt(voter_dict)
                
                # Create modal HTML
                modal_html = create_print_modal_html(receipt_text, voter_num)
                
                # Render modal (hidden by default)
                st.components.v1.html(modal_html, height=0)
                
                # Print button with JavaScript to show modal
                print_button_html = f"""
                <button 
                    onclick="document.getElementById('printModal').classList.add('active')"
                    style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 1rem;
                        font-weight: 600;
                        width: 100%;
                        transition: all 0.3s;
                    "
                    onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 10px 20px rgba(102, 126, 234, 0.3)'"
                    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'"
                >
                    🖨️ मुद्रण गर्नुहोस्<br>(Print)
                </button>
                """
                st.components.v1.html(print_button_html, height=80)

def show_results_table(data, columns):
    """Standard table display without print buttons."""
    if data.empty:
        return
    calculated_height = (len(data) + 1) * 35 
    display_height = max(150, min(calculated_height, 800))
    st.dataframe(data[columns], use_container_width=True, height=display_height, hide_index=True)

def main_app():
    st.title("🗳️ मतदाता सूची खोज प्रणाली")
    st.markdown("**Voter List Search System**")
    
    with st.sidebar:
        if st.button("🚪 Logout / बाहिर निस्कनुहोस्", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    try:
        with st.spinner('डाटा लोड गर्दै... / Loading data...'):
            df = load_data()

        display_columns = get_display_columns(df)
        
        if not display_columns:
            st.error("Excel columns missing.")
            return

        st.sidebar.header("खोज विकल्प")
        st.sidebar.markdown("---")
        st.sidebar.subheader("प्रदर्शन मोड / Display Mode")
        display_mode = st.sidebar.radio(
            "मोड छान्नुहोस्:",
            ["📋 Table View", "🖨️ Print View"],
            index=0,
            help="Print View: JavaScript popup - no reload!"
        )
        use_print_view = (display_mode == "🖨️ Print View")
        
        if use_print_view:
            st.sidebar.success("🖨️ **Print Mode**: Click opens popup!")
        
        st.sidebar.markdown("---")
        
        default_index = 7
        search_option = st.sidebar.selectbox(
            "खोज प्रकार छान्नुहोस्:",
            ["सबै डाटा हेर्नुहोस्", "मतदाताको नामबाट खोज्नुहोस्", "मतदाता नंबरबाट खोज्नुहोस्", 
             "पिता/माताको नामबाट खोज्नुहोस्", "पति/पत्नीको नामबाट खोज्नुहोस्",
             "लिङ्गबाट फिल्टर गर्नुहोस्", "उमेर दायराबाट खोज्नुहोस्", "उन्नत खोज (सबै फिल्टर)"],
            index=default_index
        )
        
        def display_results(filtered_df, display_cols):
            if use_print_view:
                show_results_table_with_print(filtered_df, display_cols)
            else:
                show_results_table(filtered_df, display_cols)
        
        if search_option == "सबै डाटा हेर्नुहोस्":
            st.subheader("सम्पूर्ण मतदाता सूची")
            display_results(df, display_columns)
            if not use_print_view:
                st.info(f"कुल मतदाता संख्या: {len(df):,}")
        
        elif search_option == "मतदाताको नामबाट खोज्नुहोस्":
            st.subheader("मतदाताको नामबाट खोज्नुहोस्")
            st.caption("🔤 उपसर्ग खोज / Prefix search")
            with st.expander("📘 उदाहरण / Examples"):
                st.markdown("**Example:** 'र' finds 'राम', 'रमेश'")
            
            search_name = st.text_input("मतदाताको नाम लेख्नुहोस्:", "", key="name_search")
            if search_name:
                filtered_df = unicode_prefix_search(df, 'मतदाताको नाम', search_name)
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("कुनै पनि मतदाता भेटिएन")
        
        elif search_option == "मतदाता नंबरबाट खोज्नुहोस्":
            st.subheader("मतदाता नंबरबाट खोज्नुहोस्")
            search_number = st.text_input("मतदाता नंबर लेख्नुहोस्:", "")
            if search_number:
                try:
                    filtered_df = df[df['मतदाता नं'] == int(search_number)]
                    if not filtered_df.empty:
                        st.success("✅ मतदाता भेटियो")
                        display_results(filtered_df, display_columns)
                    else:
                        st.warning("कुनै पनि मतदाता भेटिएन")
                except ValueError:
                    st.error("Invalid number")

        elif search_option == "पिता/माताको नामबाट खोज्नुहोस्":
            st.subheader("पिता/माताको नामबाट खोज्नुहोस्")
            search_parent = st.text_input("पिता वा माताको नाम:", "", key="parent_search")
            if search_parent:
                filtered_df = unicode_prefix_search(df, 'पिता/माताको नाम', search_parent)
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,} भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("भेटिएन")

        elif search_option == "पति/पत्नीको नामबाट खोज्नुहोस्":
            st.subheader("पति/पत्नीको नामबाट खोज्नुहोस्")
            search_spouse = st.text_input("पति वा पत्नीको नाम:", "", key="spouse_search")
            if search_spouse:
                filtered_df = unicode_prefix_search(df, 'पति/पत्नीको नाम', search_spouse)
                filtered_df = filtered_df[filtered_df['पति/पत्नीको नाम'] != '-']
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,} भेटियो")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("भेटिएन")

        elif search_option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("लिङ्गबाट फिल्टर गर्नुहोस्")
            unique_genders = [g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)]
            gender_options = ["सबै"] + list(set(unique_genders + ["पुरुष", "महिला"]))
            selected_gender = st.selectbox("लिङ्ग छान्नुहोस्:", gender_options)
            
            if selected_gender == "सबै":
                filtered_df = df
            else:
                filtered_df = df[df['लिङ्ग'] == selected_gender]
            
            if not use_print_view:
                st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
            display_results(filtered_df, display_columns)

        elif search_option == "उमेर दायराबाट खोज्नुहोस्":
            st.subheader("उमेर दायराबाट खोज्नुहोस्")
            c1, c2 = st.columns(2)
            min_age = c1.number_input("न्यूनतम:", value=18)
            max_age = c2.number_input("अधिकतम:", value=100)
            
            age_ok = df['उमेर(वर्ष)'].notna()
            in_range = (df['उमेर(वर्ष)'] >= min_age) & (df['उमेर(वर्ष)'] <= max_age)
            filtered_df = df[age_ok & in_range]
            
            if not use_print_view:
                st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
            display_results(filtered_df, display_columns)

        elif search_option == "उन्नत खोज (सबै फिल्टर)":
            st.subheader("🔍 उन्नत खोज")
            col1, col2 = st.columns(2)
            with col1:
                name_filter = st.text_input("मतदाताको नाम:", key="adv_name")
                parent_filter = st.text_input("पिता/माताको नाम:", key="adv_parent")
                spouse_filter = st.text_input("पति/पत्नीको नाम:", key="adv_spouse")
            with col2:
                genders = ["सबै"] + list(set([g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)] + ["पुरुष", "महिला"]))
                gender_filter = st.selectbox("लिङ्ग:", genders, key="adv_gender")
                ac1, ac2 = st.columns(2)
                min_age_filter = ac1.number_input("Min Age:", value=0, key="adv_min")
                max_age_filter = ac2.number_input("Max Age:", value=150, key="adv_max")

            if st.button("🔍 खोज्नुहोस्", type="primary"):
                mask = pd.Series([True] * len(df), index=df.index)
                if name_filter:
                    mask &= df['मतदाताको नाम_lower'].str.startswith(_normalize_unicode(name_filter), na=False)
                if parent_filter:
                    mask &= df['पिता/माताको नाम_lower'].str.startswith(_normalize_unicode(parent_filter), na=False)
                if spouse_filter:
                    mask &= (df['पति/पत्नीको नाम'] != '-') & df['पति/पत्नीको नाम_lower'].str.startswith(_normalize_unicode(spouse_filter), na=False)
                if gender_filter != "सबै":
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
                    st.warning("कुनै पनि मतदाता भेटिएन")

        # --- STATISTICS SECTION ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("तथ्याङ्क")
        st.sidebar.metric("कुल मतदाता", f"{len(df):,}")
        
        if 'उमेर(वर्ष)' in df.columns:
            genz_voters = df[(df['उमेर(वर्ष)'] >= 18) & (df['उमेर(वर्ष)'] <= 29)]
            st.sidebar.metric("Gen Z (18-29 वर्ष)", f"{len(genz_voters):,}")
        
        if 'लिङ्ग' in df.columns:
            st.sidebar.write("लिङ्ग अनुसार:")
            gender_counts = df['लिङ्ग'].value_counts()
            for gender, count in gender_counts.items():
                st.sidebar.write(f"- {gender}: {count:,}")
        
        if 'उमेर(वर्ष)' in df.columns:
            avg_age = df['उमेर(वर्ष)'].dropna().mean()
            st.sidebar.metric("औसत उमेर", f"{avg_age:.1f} वर्ष" if not pd.isna(avg_age) else "—")

    except FileNotFoundError:
        st.error("voterlist.xlsx not found.")
    except Exception as e:
        logger.exception("App error")
        st.error(f"Error: {str(e)}")
    
    st.markdown("---")

if not st.session_state.logged_in:
    login_page()
else:
    main_app()
