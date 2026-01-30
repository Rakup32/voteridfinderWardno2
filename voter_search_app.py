I have carefully reconstructed the voter_search_app.py code to fix the syntax error while preserving your original logic, CSS, and authentication flow.

The main change is inside the show_results_table function, where I've replaced the static table with a st.data_editor. This allows you to tick a checkbox to select a voter and immediately generate their print card.

## Integrated voter_search_app.py
Python
import logging
import unicodedata
import pandas as pd
import streamlit as st
import base64
import time
import extra_streamlit_components as stx
from credentials import USERNAME, PASSWORD
from print_logic import generate_voter_card # Import logic from your file

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

# Custom CSS (Keeping your original styles exactly)
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

STANDARD_COLUMNS = [
    'सि.नं.', 'मतदाता नं', 'मतदाताको नाम', 'उमेर(वर्ष)', 'लिङ्ग',
    'पति/पत्नीको नाम', 'पिता/माताको नाम'
]

# --- CACHE OPTIMIZATION ---
@st.cache_data(show_spinner="डाटा लोड गर्दै...")
def load_data():
    df = pd.read_excel('voterlist.xlsx')
    try:
        df.columns = df.columns.str.strip()
    except:
        df.columns = [str(c).strip() for c in df.columns]

    if 'उमेर(वर्ष)' in df.columns:
        df['उमेर(वर्ष)'] = pd.to_numeric(df['उमेर(वर्ष)'], errors='coerce')

    # Helper columns for search
    for col in ['मतदाताको नाम', 'पिता/माताको नाम', 'पति/पत्नीको नाम']:
        if col in df.columns:
            df[f'{col}_lower'] = df[col].astype(str).map(_normalize_unicode)
    return df

def get_display_columns(df):
    final_cols = [c for c in STANDARD_COLUMNS if c in df.columns]
    for c in df.columns:
        if c not in final_cols and not c.endswith('_lower'):
            final_cols.append(c)
    return final_cols

def unicode_prefix_search(df, column, search_term):
    if not search_term or column not in df.columns:
        return df
    normalized = _normalize_unicode(search_term)
    lower_col = column + "_lower"
    return df[df[lower_col].str.startswith(normalized, na=False)]

# --- NEW: TICK ROW TO PRINT POPUP ---
def show_results_table(data, columns):
    """Adds a checkbox column. Ticking a row triggers print_logic.py."""
    if data.empty:
        return

    st.info("💡 प्रिन्ट गर्नको लागि बायाँ पट्टीको बाकस (Box) मा टिक लगाउनुहोस्।")
    
    # We add a 'Select' column for checkboxes
    display_df = data[columns].copy()
    display_df.insert(0, "Select", False)

    # Use data_editor for the interactive tick box
    edited_df = st.data_editor(
        display_df,
        column_config={"Select": st.column_config.CheckboxColumn("Print", default=False)},
        disabled=columns, # Only 'Select' is editable
        hide_index=True,
        use_container_width=True,
        key=f"editor_{hash(str(data.index))}"
    )

    # Check if any row is ticked
    selected_indices = edited_df.index[edited_df["Select"] == True].tolist()
    
    if selected_indices:
        # Get data from the original dataframe based on edited_df selection
        for idx in selected_indices:
            row_data = data.iloc[idx]
            st.markdown(f"### प्रिन्ट प्रिभ्यू (Print Preview): {row_data['मतदाताको नाम']}")
            generate_voter_card(row_data)

def main_app():
    st.title("🗳️ मतदाता सूची खोज प्रणाली")
    st.markdown("**Voter List Search System**")
    
    with st.sidebar:
        if st.button("🚪 Logout / बाहिर निस्कनुहोस्", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    try:
        df = load_data()
        display_columns = get_display_columns(df)
        
        st.sidebar.header("खोज विकल्प")
        search_option = st.sidebar.selectbox(
            "खोज प्रकार छान्नुहोस्:",
            ["मतदाताको नामबाट", "मतदाता नंबरबाट", "सबै"],
            index=0
        )
        
        filtered_df = df
        if search_option == "मतदाताको नामबाट":
            name_q = st.text_input("नाम लेख्नुहोस्:")
            if name_q:
                filtered_df = unicode_prefix_search(df, 'मतदाताको नाम', name_q)
        elif search_option == "मतदाता नंबरबाट":
            num_q = st.text_input("नंबर लेख्नुहोस्:")
            if num_q:
                filtered_df = df[df['मतदाता नं'].astype(str) == num_q]

        show_results_table(filtered_df, display_columns)

    except Exception as e:
        st.error(f"Error logic failed: {e}")

if not st.session_state.logged_in:
    login_page()
else:
    main_app()