import logging
import unicodedata
import pandas as pd
import streamlit as st
import base64
import time
import extra_streamlit_components as stx
from credentials import USERNAME, PASSWORD
from print_logic import format_voter_receipt, show_print_dialog, create_print_preview

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

# Custom CSS
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
    .voter-card { background: #f7fafc; border: 1px solid #e2e8f0; padding: 0.75rem; margin: 0.5rem 0; border-radius: 6px; }
    @media screen and (max-width: 768px) { .main { padding: 0.5rem 0.75rem; } h1 { font-size: 1.35rem !important; } }
    @media screen and (max-width: 480px) { .main { padding: 0.4rem 0.5rem; } h1 { font-size: 1.2rem !important; } }
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
    # These will be hidden from the final view automatically
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
    Preserves the order of STANDARD_COLUMNS first, then appends any new columns found.
    """
    # 1. Start with standard columns if they exist in the file
    final_cols = [c for c in STANDARD_COLUMNS if c in df.columns]
    
    # 2. Add any columns NOT in standard list, NOT ending in _lower
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
    
    # Check if helper column exists
    lower_col = column + "_lower"
    if lower_col not in df.columns:
        return df
        
    mask = df[lower_col].str.startswith(normalized, na=False)
    return df[mask]

def _build_modal_block(receipt_text, voter_num):
    """
    Return a single HTML string that contains BOTH the print button AND
    the modal popup.  Everything lives in one <div> so that when Streamlit
    renders it via st.components.v1.html() it lands in ONE iframe and the
    JavaScript onclick can reach the modal without any cross-iframe issues.
    """
    import json                          # safe escaping for JS string literals
    receipt_js   = json.dumps(receipt_text)   # adds quotes + escapes everything
    voter_num_js = json.dumps(str(voter_num))

    # A printable HTML page that thermal printers can use
    # We embed it as a JS template string so window.open can write it
    print_page = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8">'
        '<style>'
        '@page{size:58mm auto;margin:5mm}'
        'body{font-family:"Courier New",monospace;font-size:11pt;'
        'line-height:1.5;width:58mm;margin:0 auto;padding:5mm}'
        'pre{white-space:pre-wrap;word-wrap:break-word;'
        'font-family:"Courier New",monospace;font-size:11pt;margin:0}'
        '</style></head><body><pre>' +
        receipt_text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;') +
        '</pre></body></html>'
    )
    print_page_js = json.dumps(print_page)

    return f"""
<div style="width:100%;">

<!-- ====== PRINT BUTTON (always visible) ====== -->
<button id="openBtn"
  onclick="document.getElementById('modalBg').style.display='flex'"
  style="
    width:100%;padding:14px 8px;border:none;border-radius:8px;cursor:pointer;
    background:linear-gradient(135deg,#667eea,#764ba2);
    color:#fff;font-size:15px;font-weight:600;line-height:1.4;
    transition:transform .2s,box-shadow .2s;
  "
  onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 16px rgba(102,126,234,.4)'"
  onmouseout ="this.style.transform='translateY(0)' ;this.style.boxShadow='none'"
>🖨️ मुद्रण गर्नुहोस्<br><span style="font-size:13px;opacity:.85">(Print)</span></button>

<!-- ====== MODAL OVERLAY (hidden until button clicked) ====== -->
<div id="modalBg" style="
  display:none;position:fixed;top:0;left:0;width:100%;height:100%;
  background:rgba(0,0,0,.72);z-index:99999;
  justify-content:center;align-items:center;
">
  <div style="
    background:#fff;border-radius:14px;width:95%;max-width:720px;
    max-height:92vh;overflow-y:auto;box-shadow:0 30px 60px rgba(0,0,0,.4);
    animation:slideDown .25s ease;
  ">
    <!-- header -->
    <div style="
      background:linear-gradient(135deg,#667eea,#764ba2);
      color:#fff;padding:18px 22px;border-radius:14px 14px 0 0;
    ">
      <h2 style="margin:0;font-size:1.35rem;">🖨️ मुद्रण पूर्वावलोकन / Print Preview</h2>
      <p style="margin:6px 0 0;opacity:.85;font-size:.88rem;">
        मतदाता नं: {voter_num} &nbsp;|&nbsp; 58mm Thermal Printer
      </p>
    </div>

    <!-- body -->
    <div style="padding:20px 22px 24px;">

      <!-- receipt box -->
      <div style="
        background:#f7fafc;border:2px solid #e2e8f0;border-radius:8px;
        padding:18px 20px;font-family:'Courier New',monospace;font-size:1.1rem;
        white-space:pre-wrap;line-height:1.6;max-height:500px;overflow-y:auto;
        margin-bottom:20px;
      ">{receipt_text}</div>

      <!-- 3 action buttons -->
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px;">

        <!-- Browser Print -->
        <button onclick="doPrint()" style="
          background:linear-gradient(135deg,#38b2ac,#319795);
          color:#fff;border:none;border-radius:8px;padding:14px 6px;
          cursor:pointer;font-size:.88rem;font-weight:600;text-align:center;
          transition:transform .2s,box-shadow .2s;
        "
          onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 12px rgba(56,178,172,.35)'"
          onmouseout ="this.style.transform='translateY(0)' ;this.style.boxShadow='none'"
        >🖨️<br><strong>Browser Print</strong><br><span style="font-size:.78rem;opacity:.85">Instant!</span></button>

        <!-- Download TXT -->
        <button onclick="dlTXT()" style="
          background:linear-gradient(135deg,#4299e1,#3182ce);
          color:#fff;border:none;border-radius:8px;padding:14px 6px;
          cursor:pointer;font-size:.88rem;font-weight:600;text-align:center;
          transition:transform .2s,box-shadow .2s;
        "
          onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 12px rgba(66,153,225,.35)'"
          onmouseout ="this.style.transform='translateY(0)' ;this.style.boxShadow='none'"
        >💾<br><strong>Download TXT</strong><br><span style="font-size:.78rem;opacity:.85">For thermal</span></button>

        <!-- Download HTML -->
        <button onclick="dlHTML()" style="
          background:linear-gradient(135deg,#4299e1,#3182ce);
          color:#fff;border:none;border-radius:8px;padding:14px 6px;
          cursor:pointer;font-size:.88rem;font-weight:600;text-align:center;
          transition:transform .2s,box-shadow .2s;
        "
          onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 12px rgba(66,153,225,.35)'"
          onmouseout ="this.style.transform='translateY(0)' ;this.style.boxShadow='none'"
        >📄<br><strong>Download HTML</strong><br><span style="font-size:.78rem;opacity:.85">Best format</span></button>
      </div>

      <!-- Close button -->
      <button onclick="document.getElementById('modalBg').style.display='none'" style="
        width:100%;padding:12px;border:none;border-radius:8px;cursor:pointer;
        background:linear-gradient(135deg,#f56565,#e53e3e);
        color:#fff;font-size:.95rem;font-weight:600;
        transition:transform .2s,box-shadow .2s;
      "
        onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 12px rgba(245,101,101,.35)'"
        onmouseout ="this.style.transform='translateY(0)' ;this.style.boxShadow='none'"
      >❌ बन्द गर्नुहोस् (Close)</button>
    </div>
  </div>
</div>

<!-- ====== click-outside closes modal ====== -->
<script>
(function(){{
  var bg = document.getElementById('modalBg');
  bg.addEventListener('click', function(e){{
    if(e.target === bg) bg.style.display = 'none';
  }});

  // ESC key closes modal
  document.addEventListener('keydown', function(e){{
    if(e.key === 'Escape') bg.style.display = 'none';
  }});

  var receiptText = {receipt_js};
  var voterNum    = {voter_num_js};
  var printPage   = {print_page_js};

  function doPrint(){{
    var w = window.open('','_blank','width=400,height=700');
    w.document.write(printPage);
    w.document.close();
    w.focus();
    setTimeout(function(){{ w.print(); w.close(); }}, 300);
  }}

  function dlTXT(){{
    var b = new Blob([receiptText],{{type:'text/plain;charset=utf-8'}});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(b);
    a.download = 'voter_' + voterNum + '.txt';
    a.click();
  }}

  function dlHTML(){{
    var b = new Blob([printPage],{{type:'text/html;charset=utf-8'}});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(b);
    a.download = 'voter_' + voterNum + '.html';
    a.click();
  }}
}})();
</script>

<style>
  @keyframes slideDown{{
    from{{ opacity:0; transform:translateY(-40px); }}
    to  {{ opacity:1; transform:translateY(0);     }}
  }}
</style>
</div>
"""


def show_results_table_with_print(data, columns):
    """Display results with a JS-modal print popup — zero page reload."""
    if data.empty:
        return

    st.markdown("""
    <div class="print-info-box">
        <strong>🖨️ प्रिन्ट मोड सक्रिय छ / Print Mode Active</strong><br>
        📋 प्रत्येक मतदातामा क्लिक गर्नुहोस् र Print बटन थिच्नुहोस्।<br>
        💡 पॉपআপ खुल्छ — पेज रिलोड हुन्छन् नैन।
    </div>
    """, unsafe_allow_html=True)

    st.caption(f"📊 कुल मतदाता: {len(data):,}")

    for idx, row in data.iterrows():
        voter_name = row.get('मतदाताको नाम', 'N/A')
        voter_num  = row.get('मतदाता नं',    'N/A')

        with st.expander(f"🗳️ {voter_name} — मतदाता नं: {voter_num}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                for col in columns:
                    if col in row.index and col != 'मतदाता विवरणहरू':
                        value = row[col] if pd.notna(row[col]) else '-'
                        st.text(f"{col}: {value}")

            with col2:
                # Generate the receipt once
                voter_dict   = row.to_dict()
                receipt_text = format_voter_receipt(voter_dict)

                # Single HTML block: button + modal in one iframe
                modal_html = _build_modal_block(receipt_text, voter_num)
                st.components.v1.html(modal_html, height=80, scrolling=False)

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

        # Get all valid display columns (Standard + Any New Columns)
        display_columns = get_display_columns(df)
        
        if not display_columns:
            st.error("Excel columns missing.")
            return

        st.sidebar.header("खोज विकल्प")
        
        # Add display mode toggle
        st.sidebar.markdown("---")
        st.sidebar.subheader("प्रदर्शन मोड / Display Mode")
        display_mode = st.sidebar.radio(
            "मोड छान्नुहोस् / Select Mode:",
            ["📋 Table View (तालिका)", "🖨️ Print View (प्रिन्ट)"],
            index=0,
            help="Table View: सबै मतदाता एकै पटक हेर्नुहोस् | Print View: प्रत्येक मतदाता प्रिन्ट गर्न सकिन्छ"
        )
        use_print_view = (display_mode == "🖨️ Print View (प्रिन्ट)")
        
        if use_print_view:
            st.sidebar.info("🖨️ **Print Mode Active**\n\nप्रत्येक मतदातामा Print बटन देखिनेछ।\nEach voter will have a Print button.")
        
        st.sidebar.markdown("---")
        
        default_index = 7
        search_option = st.sidebar.selectbox(
            "खोज प्रकार छान्नुहोस्:",
            ["सबै डाटा हेर्नुहोस्", "मतदाताको नामबाट खोज्नुहोस्", "मतदाता नंबरबाट खोज्नुहोस्", 
             "पिता/माताको नामबाट खोज्नुहोस्", "पति/पत्नीको नामबाट खोज्नुहोस्",
             "लिङ्गबाट फिल्टर गर्नुहोस्", "उमेर दायराबाट खोज्नुहोस्", "उन्नत खोज (सबै फिल्टर)"],
            index=default_index
        )
        
        # Helper function to show results based on mode
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
        # ---------------------------------------------

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
