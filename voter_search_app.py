import logging
import unicodedata
import pandas as pd
import streamlit as st
import base64
import time
import re
import extra_streamlit_components as stx
from credentials import USERNAME, PASSWORD
from print_logic import format_voter_receipt, show_print_dialog, create_print_preview

# Try to import Aksharamukha
try:
    from aksharamukha import transliterate
    AKSHARAMUKHA_AVAILABLE = True
except ImportError:
    AKSHARAMUKHA_AVAILABLE = False

# ============================================================================
# IMPROVED ROMAN TO DEVANAGARI CONVERTER
# ============================================================================

# Custom mappings for common Nepali names (exact matching)
import roman_to_nepali 
@st.cache_data(ttl=3600, show_spinner=False)
def roman_to_devanagari(text: str) -> str:
    """
    Convert Roman Nepali to Devanagari.
    Priority: Custom mappings > Aksharamukha ITRANS > Return as-is
    """
    if not text or not isinstance(text, str):
        return text
    
    text = text.strip()
    
    # Already Devanagari? Return as-is
    if re.search(r'[\u0900-\u097F]', text):
        return text
    
    text_lower = text.lower()
    
    # Try exact match from custom mappings
    if text_lower in COMMON_NAMES:
        return COMMON_NAMES[text_lower]
    
    # Try multi-word conversion
    words = text_lower.split()
    if len(words) > 1:
        converted_words = []
        for word in words:
            if word in COMMON_NAMES:
                converted_words.append(COMMON_NAMES[word])
            elif AKSHARAMUKHA_AVAILABLE:
                try:
                    result = transliterate.process('ITRANS', 'Devanagari', word)
                    converted_words.append(result if result else word)
                except:
                    converted_words.append(word)
            else:
                converted_words.append(word)
        return ' '.join(converted_words)
    
    # Single word - try Aksharamukha
    if AKSHARAMUKHA_AVAILABLE:
        try:
            result = transliterate.process('ITRANS', 'Devanagari', text_lower)
            return result if result else text
        except:
            pass
    
    # Fallback: return original
    return text

# ============================================================================
# ORIGINAL CODE
# ============================================================================

def _normalize_unicode(s):
    """Normalize to NFC for consistent Unicode-aware Nepali character comparison."""
    if not isinstance(s, str) or not s:
        return s
    return unicodedata.normalize("NFC", s.strip().lower())

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="मतदाता सूची खोज प्रणाली",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="auto"
)

cookie_manager = stx.CookieManager()

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError) as e:
        logger.debug("Image not loaded: %s - %s", image_path, e)
        return None

bell_image_base64 = get_base64_image("bell.png")

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
    final_cols = [c for c in STANDARD_COLUMNS if c in df.columns]
    for c in df.columns:
        if c not in STANDARD_COLUMNS and not c.endswith('_lower') and c not in final_cols:
            final_cols.append(c)
    return final_cols

def unicode_prefix_search(df, column, search_term):
    if not search_term or column not in df.columns:
        return df
    
    # Convert Roman to Devanagari
    search_term = roman_to_devanagari(search_term)
    
    normalized = _normalize_unicode(search_term)
    if not normalized:
        return df
    
    lower_col = column + "_lower"
    if lower_col not in df.columns:
        return df
        
    mask = df[lower_col].str.startswith(normalized, na=False)
    return df[mask]

def show_results_table_with_print(data, columns):
    if data.empty:
        return
    
    if 'print_preview_states' not in st.session_state:
        st.session_state.print_preview_states = {}
    
    st.markdown("""
    <div class="print-info-box">
        <strong>🖨️ प्रिन्ट मोड सक्रिय छ / Print Mode Active</strong><br>
        📋 प्रत्येक मतदातामा क्लिक गर्नुहोस् र Print बटन थिच्नुहोस्।
    </div>
    """, unsafe_allow_html=True)
    
    st.caption(f"📊 कुल मतदाता: {len(data):,}")
    
    for idx, row in data.iterrows():
        voter_name = row.get('मतदाताको नाम', 'N/A')
        voter_num = row.get('मतदाता नं', 'N/A')
        voter_key = f"voter_{voter_num}"
        
        with st.expander(f"🗳️ {voter_name} — मतदाता नं: {voter_num}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown('<div class="voter-card">', unsafe_allow_html=True)
                for col in columns:
                    if col in row.index:
                        value = row[col] if pd.notna(row[col]) else '-'
                        st.text(f"{col}: {value}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                if st.button("🖨️ मुद्रण", key=f"print_btn_{voter_key}", use_container_width=True):
                    st.session_state.print_preview_states[voter_key] = True
                    st.rerun()
            
            if st.session_state.print_preview_states.get(voter_key, False):
                st.markdown("---")
                voter_dict = row.to_dict()
                receipt_text = format_voter_receipt(voter_dict)
                st.code(receipt_text, language=None)
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button(
                        label="💾 डाउनलोड",
                        data=receipt_text,
                        file_name=f"voter_{voter_num}.txt",
                        mime="text/plain",
                        key=f"download_{voter_key}",
                        use_container_width=True
                    )
                with col_d2:
                    if st.button("❌ बन्द", key=f"close_{voter_key}", use_container_width=True):
                        st.session_state.print_preview_states[voter_key] = False
                        st.rerun()

def show_results_table(data, columns):
    if data.empty:
        return
    calculated_height = (len(data) + 1) * 35 
    display_height = max(150, min(calculated_height, 800))
    st.dataframe(data[columns], use_container_width=True, height=display_height, hide_index=True)

def main_app():
    st.title("🗳️ मतदाता सूची खोज प्रणाली")
    st.markdown("**Voter List Search System**")
    
    # Show Roman typing status
    if len(COMMON_NAMES) > 0:
        st.info(f"💡 **Roman Typing Enabled** ({len(COMMON_NAMES)} names mapped) - Type 'ram', 'pukar', 'samjhana', etc.")
    
    with st.sidebar:
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    try:
        with st.spinner('Loading...'):
            df = load_data()

        display_columns = get_display_columns(df)
        
        if not display_columns:
            st.error("Excel columns missing.")
            return

        st.sidebar.header("खोज विकल्प")
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("प्रदर्शन मोड")
        display_mode = st.sidebar.radio(
            "मोड:",
            ["📋 Table View", "🖨️ Print View"],
            index=0
        )
        use_print_view = (display_mode == "🖨️ Print View")
        
        st.sidebar.markdown("---")
        
        search_option = st.sidebar.selectbox(
            "खोज प्रकार:",
            ["सबै डाटा हेर्नुहोस्", "मतदाताको नामबाट खोज्नुहोस्", "मतदाता नंबरबाट खोज्नुहोस्", 
             "पिता/माताको नामबाट खोज्नुहोस्", "पति/पत्नीको नामबाट खोज्नुहोस्",
             "लिङ्गबाट फिल्टर गर्नुहोस्", "उमेर दायराबाट खोज्नुहोस्", "उन्नत खोज (सबै फिल्टर)"],
            index=7
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
                st.info(f"कुल: {len(df):,}")
        
        elif search_option == "मतदाताको नामबाट खोज्नुहोस्":
            st.subheader("मतदाताको नामबाट खोज्नुहोस्")
            st.caption("Type in Nepali or Roman (ram, pukar, samjhana)")
            
            search_name = st.text_input("नाम:", "", key="name_search")
            if search_name:
                filtered_df = unicode_prefix_search(df, 'मतदाताको नाम', search_name)
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,} found")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("Not found")
        
        elif search_option == "मतदाता नंबरबाट खोज्नुहोस्":
            st.subheader("मतदाता नंबरबाट खोज्नुहोस्")
            search_number = st.text_input("नंबर:", "")
            if search_number:
                try:
                    filtered_df = df[df['मतदाता नं'] == int(search_number)]
                    if not filtered_df.empty:
                        st.success("✅ Found")
                        display_results(filtered_df, display_columns)
                    else:
                        st.warning("Not found")
                except ValueError:
                    st.error("Invalid number")

        elif search_option == "पिता/माताको नामबाट खोज्नुहोस्":
            st.subheader("पिता/माताको नामबाट खोज्नुहोस्")
            st.caption("Nepali or Roman")
            search_parent = st.text_input("नाम:", "", key="parent_search")
            if search_parent:
                filtered_df = unicode_prefix_search(df, 'पिता/माताको नाम', search_parent)
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,}")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("Not found")

        elif search_option == "पति/पत्नीको नामबाट खोज्नुहोस्":
            st.subheader("पति/पत्नीको नामबाट खोज्नुहोस्")
            search_spouse = st.text_input("नाम:", "", key="spouse_search")
            if search_spouse:
                filtered_df = unicode_prefix_search(df, 'पति/पत्नीको नाम', search_spouse)
                filtered_df = filtered_df[filtered_df['पति/पत्नीको नाम'] != '-']
                if not filtered_df.empty:
                    if not use_print_view:
                        st.success(f"✅ {len(filtered_df):,}")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("Not found")

        elif search_option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("लिङ्गबाट फिल्टर")
            unique_genders = [g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)]
            gender_options = ["सबै"] + list(set(unique_genders + ["पुरुष", "महिला"]))
            selected_gender = st.selectbox("लिङ्ग:", gender_options)
            
            if selected_gender == "सबै":
                filtered_df = df
            else:
                filtered_df = df[df['लिङ्ग'] == selected_gender]
            
            if not use_print_view:
                st.success(f"✅ {len(filtered_df):,}")
            display_results(filtered_df, display_columns)

        elif search_option == "उमेर दायराबाट खोज्नुहोस्":
            st.subheader("उमेर दायरा")
            c1, c2 = st.columns(2)
            min_age = c1.number_input("Min:", value=18)
            max_age = c2.number_input("Max:", value=100)
            
            age_ok = df['उमेर(वर्ष)'].notna()
            in_range = (df['उमेर(वर्ष)'] >= min_age) & (df['उमेर(वर्ष)'] <= max_age)
            filtered_df = df[age_ok & in_range]
            
            if not use_print_view:
                st.success(f"✅ {len(filtered_df):,}")
            display_results(filtered_df, display_columns)

        elif search_option == "उन्नत खोज (सबै फिल्टर)":
            st.subheader("🔍 उन्नत खोज")
            st.caption("All fields support Roman typing")
            col1, col2 = st.columns(2)
            with col1:
                name_filter = st.text_input("मतदाता:", key="adv_name")
                parent_filter = st.text_input("पिता/माता:", key="adv_parent")
                spouse_filter = st.text_input("पति/पत्नी:", key="adv_spouse")
            with col2:
                genders = ["सबै"] + list(set([g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)] + ["पुरुष", "महिला"]))
                gender_filter = st.selectbox("लिङ्ग:", genders, key="adv_gender")
                ac1, ac2 = st.columns(2)
                min_age_filter = ac1.number_input("Min Age:", value=0, key="adv_min")
                max_age_filter = ac2.number_input("Max Age:", value=150, key="adv_max")

            if st.button("🔍 Search", type="primary"):
                mask = pd.Series([True] * len(df), index=df.index)
                if name_filter:
                    name_filter = roman_to_devanagari(name_filter)
                    mask &= df['मतदाताको नाम_lower'].str.startswith(_normalize_unicode(name_filter), na=False)
                if parent_filter:
                    parent_filter = roman_to_devanagari(parent_filter)
                    mask &= df['पिता/माताको नाम_lower'].str.startswith(_normalize_unicode(parent_filter), na=False)
                if spouse_filter:
                    spouse_filter = roman_to_devanagari(spouse_filter)
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
                        st.success(f"✅ {len(filtered_df):,}")
                    display_results(filtered_df, display_columns)
                else:
                    st.warning("Not found")

        st.sidebar.markdown("---")
        st.sidebar.subheader("तथ्याङ्क")
        st.sidebar.metric("कुल", f"{len(df):,}")
        
        if 'उमेर(वर्ष)' in df.columns:
            genz_voters = df[(df['उमेर(वर्ष)'] >= 18) & (df['उमेर(वर्ष)'] <= 29)]
            st.sidebar.metric("Gen Z (18-29)", f"{len(genz_voters):,}")
        
        if 'लिङ्ग' in df.columns:
            st.sidebar.write("लिङ्ग:")
            gender_counts = df['लिङ्ग'].value_counts()
            for gender, count in gender_counts.items():
                st.sidebar.write(f"- {gender}: {count:,}")
        
        if 'उमेर(वर्ष)' in df.columns:
            avg_age = df['उमेर(वर्ष)'].dropna().mean()
            st.sidebar.metric("औसत उमेर", f"{avg_age:.1f}" if not pd.isna(avg_age) else "—")

    except FileNotFoundError:
        st.error("voterlist.xlsx not found.")
    except Exception as e:
        logger.exception("Error")
        st.error(f"Error: {str(e)}")
    
    st.markdown("---")

if not st.session_state.logged_in:
    login_page()
else:
    main_app()