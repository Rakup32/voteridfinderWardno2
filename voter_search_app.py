import logging
import unicodedata
import pandas as pd
import streamlit as st
import base64
from credentials import USERNAME, PASSWORD


def _normalize_unicode(s):
    """Normalize to NFC for consistent Unicode-aware Nepali character comparison."""
    if not isinstance(s, str) or not s:
        return s
    return unicodedata.normalize("NFC", s.strip().lower())

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Set page configuration (mobile-friendly: collapsed sidebar on small screens)
st.set_page_config(
    page_title="मतदाता सूची खोज प्रणाली",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="auto"  # Collapsed on mobile, expanded on desktop
)

# Function to convert image to base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError) as e:
        logger.debug("Image not loaded: %s - %s", image_path, e)
        return None

# Get base64 encoded bell image
bell_image_base64 = get_base64_image("bell.png")

# Custom CSS: realistic login + full mobile support
st.markdown("""
    <style>
    /* ========== Base & mobile-first ========== */
    .main { padding: 0.75rem 1rem; max-width: 100%; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    h1 { color: #c53030; text-align: center; padding: 0.75rem 0; word-break: break-word; }
    h2, h3 { word-break: break-word; }

    /* Touch-friendly inputs and buttons (min 44px) */
    .stTextInput input, .stNumberInput input { min-height: 44px !important; font-size: 16px !important; }
    .stButton > button { min-height: 44px !important; padding: 0.5rem 1rem !important; font-size: 1rem !important; }
    .stSelectbox > div { min-height: 44px !important; }

    /* Sidebar: full width on small screens, comfortable on desktop */
    [data-testid="stSidebar"] { min-width: 260px; }
    [data-testid="stSidebar"] .stSelectbox { width: 100%; }

    /* ========== Login page: centered, logo swing, form visible (no 100vh so form is not below fold) ========== */
    .login-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1rem 1rem 0.5rem;
        box-sizing: border-box;
    }
    .login-card {
        width: 100%;
        max-width: 560px;
        padding: 2rem 1.75rem 0;
        text-align: center;
        margin: 0 auto;
        margin-bottom: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .login-header-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        width: 100%;
        max-width: 560px;
        margin-left: auto;
        margin-right: auto;
    }
    .login-logo {
        width: 80px;
        height: 80px;
        margin: 0 auto 1rem;
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        background: #f7fafc;
        animation: login-swing 2s ease-in-out infinite;
    }
    .login-logo img { width: 100%; height: 100%; object-fit: contain; }
    @keyframes login-swing {
        0%, 100% { transform: rotate(0deg); }
        25% { transform: rotate(8deg); }
        75% { transform: rotate(-8deg); }
    }
    .login-badge {
        display: block;
        font-size: 0.7rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
        text-align: center;
    }
    .login-title { color: #2d3748; font-size: 1.25rem; font-weight: 700; margin-bottom: 0.3rem; line-height: 1.3; text-align: center; word-wrap: break-word; overflow-wrap: break-word; }
    .login-subtitle { color: #c53030; font-size: 1rem; font-weight: 600; margin-bottom: 0.2rem; text-align: center; word-wrap: break-word; overflow-wrap: break-word; }
    .login-subtitle-en { color: #718096; font-size: 0.9rem; margin-bottom: 0.5rem; text-align: center; word-wrap: break-word; overflow-wrap: break-word; }
    .login-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 0.5rem auto 0.25rem;
        max-width: 400px;
        width: 100%;
    }
    .login-footer {
        margin-top: 1.5rem;
        font-size: 0.75rem;
        color: #a0aec0;
        text-align: center;
        margin-left: auto;
        margin-right: auto;
    }
    /* No gap: header text flows straight into form (प्रयोगकर्ता नाम / Username) */
    .main .block-container > div:has(.login-wrapper) { margin-bottom: 0 !important; padding-bottom: 0 !important; }
    .main .block-container > div:has([data-testid="stForm"]) { margin-top: 0 !important; padding-top: 0 !important; }
    [class*="e10yg2by1"]:has(.login-wrapper), [class*="qcpnpn"]:has(.login-wrapper) { margin-bottom: 0 !important; padding-bottom: 0 !important; }
    .main [data-testid="stForm"] { max-width: 400px; margin-left: auto !important; margin-right: auto !important; margin-top: 0 !important; padding-top: 0 !important; }
    .main [data-testid="stForm"] > div { padding-top: 0 !important; margin-top: 0 !important; }
    .main .stAlert { max-width: 480px; margin-left: auto; margin-right: auto; }

    /* ========== Mobile: app-wide ========== */
    @media screen and (max-width: 768px) {
        .main { padding: 0.5rem 0.75rem; }
        h1 { font-size: 1.35rem !important; }
        h2 { font-size: 1.15rem !important; }
        h3 { font-size: 0.95rem !important; }
        .stDataFrame { font-size: 0.85rem; }
        [data-testid="stSidebar"] { min-width: 100%; width: 100%; }
    }
    @media screen and (max-width: 480px) {
        .main { padding: 0.4rem 0.5rem; }
        h1 { font-size: 1.2rem !important; }
        .login-card, .login-header-wrap { max-width: 100%; padding: 1.5rem 1rem; }
        .login-title { font-size: 1.1rem; }
        .login-subtitle { font-size: 0.95rem; }
        .login-subtitle-en { font-size: 0.85rem; }
        .login-logo { width: 60px; height: 60px; }
    }

    /* Main app: prevent horizontal scroll on mobile */
    .block-container { max-width: 100%; padding-left: 1rem; padding-right: 1rem; }
    @media (max-width: 768px) {
        .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
        [data-testid="stDataFrame"] { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    }
    @media (max-width: 480px) {
        .block-container { padding-left: 0.5rem; padding-right: 0.5rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Login function
def check_login(username, password):
    if not USERNAME and not PASSWORD:
        return False  # Credentials not configured
    return username == USERNAME and password == PASSWORD

# Login page (realistic card, mobile-friendly)
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
                st.error("लगइन सेटअप भएको छैन। VOTER_APP_USERNAME र VOTER_APP_PASSWORD .env मा सेट गर्नुहोस्।")
            elif check_login(username, password):
                st.session_state.logged_in = True
                st.success("लगइन सफल भयो!")
                st.balloons()
                st.rerun()
            else:
                st.error("गलत प्रयोगकर्ता नाम वा पासवर्ड।")

    st.markdown('<div class="login-footer">Official use only • Authorized personnel</div>', unsafe_allow_html=True)

# Logout function
def logout():
    st.session_state.logged_in = False
    st.rerun()

# Expected display columns (order preserved; only existing columns are used)
EXPECTED_DISPLAY_COLUMNS = [
    'सि.नं.', 'मतदाता नं', 'मतदाताको नाम', 'उमेर(वर्ष)', 'लिङ्ग',
    'पति/पत्नीको नाम', 'पिता/माताको नाम'
]

# Optimized data loading with preprocessing
@st.cache_data
def load_data():
    df = pd.read_excel('voterlist.xlsx')
    # Normalize column names (strip whitespace) to avoid KeyError from Excel quirks
    try:
        df.columns = df.columns.str.strip()
    except AttributeError:
        df.columns = [str(c).strip() for c in df.columns]

    # Ensure age column is numeric; NaN kept for filtering (excluded from age range)
    if 'उमेर(वर्ष)' in df.columns:
        df['उमेर(वर्ष)'] = pd.to_numeric(df['उमेर(वर्ष)'], errors='coerce')

    # Unicode-aware normalized lowercase for prefix search (NFC for Nepali)
    df['मतदाताको नाम_lower'] = df['मतदाताको नाम'].astype(str).map(lambda s: _normalize_unicode(s))
    df['पिता/माताको नाम_lower'] = df['पिता/माताको नाम'].astype(str).map(lambda s: _normalize_unicode(s))
    df['पति/पत्नीको नाम_lower'] = df['पति/पत्नीको नाम'].astype(str).map(lambda s: _normalize_unicode(s))

    # Fill NaN values for faster filtering
    df['पति/पत्नीको नाम'] = df['पति/पत्नीको नाम'].fillna('-')
    df['पति/पत्नीको नाम_lower'] = df['पति/पत्नीको नाम_lower'].fillna('-')

    return df


def get_display_columns(df):
    """Return only columns that exist in df, in expected order."""
    valid = [c for c in EXPECTED_DISPLAY_COLUMNS if c in df.columns]
    if len(valid) < len(EXPECTED_DISPLAY_COLUMNS):
        missing = set(EXPECTED_DISPLAY_COLUMNS) - set(valid)
        logger.warning("Some expected columns missing in Excel: %s", missing)
    return valid

# Unicode-aware prefix matching (startswith) for Nepali character sequence search
def unicode_prefix_search(df, column, search_term):
    """
    Match rows where the column value starts with the search term.
    Uses NFC normalization so Nepali character sequences compare correctly.
    """
    if not search_term:
        return df
    normalized = _normalize_unicode(search_term)
    if not normalized:
        return df
    lower_col = column + "_lower"
    mask = df[lower_col].str.startswith(normalized, na=False)
    return df[mask]

# Main app (only shown after login)
def main_app():
    # Render title and UI first so the page is never blank
    st.title("🗳️ मतदाता सूची खोज प्रणाली")
    st.markdown("**Voter List Search System**")
    
    with st.sidebar:
        if st.button("🚪 Logout / बाहिर निस्कनुहोस्", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    try:
        with st.spinner('डाटा लोड गर्दै... / Loading data...'):
            df = load_data()

        # Display columns that exist in the loaded data
        display_columns = get_display_columns(df)
        if not display_columns:
            st.error("Excel मा अपेक्षित कुनै स्तम्भ भेटिएन। कृपया voterlist.xlsx फर्म्याट जाँच्नुहोस्।")
            st.markdown("---")
            st.markdown("**नोट:** यो एक मतदाता सूची खोज प्रणाली हो। सबै डाटा मूल Excel फाइलबाट लिइएको छ।")
            return

        # Sidebar for search options
        st.sidebar.header("खोज विकल्प")
        
        # Set default to advanced search on first load
        default_index = 7  # Index for "उन्नत खोज (सबै फिल्टर)"
        
        search_option = st.sidebar.selectbox(
            "खोज प्रकार छान्नुहोस्:",
            ["सबै डाटा हेर्नुहोस्", "मतदाताको नामबाट खोज्नुहोस्", "मतदाता नंबरबाट खोज्नुहोस्", 
             "पिता/माताको नामबाट खोज्नुहोस्", "पति/पत्नीको नामबाट खोज्नुहोस्",
             "लिङ्गबाट फिल्टर गर्नुहोस्", "उमेर दायराबाट खोज्नुहोस्", "उन्नत खोज (सबै फिल्टर)"],
            index=default_index
        )
        
        # Display based on search option
        if search_option == "सबै डाटा हेर्नुहोस्":
            st.subheader("सम्पूर्ण मतदाता सूची")
            st.dataframe(df[display_columns], use_container_width=True, height=600)
            st.info(f"कुल मतदाता संख्या: {len(df):,}")
        
        elif search_option == "मतदाताको नामबाट खोज्नुहोस्":
            st.subheader("मतदाताको नामबाट खोज्नुहोस्")
            st.caption("🔤 उपसर्ग खोज: नाम सुरुको अक्षरले मेल खान्छ / Prefix search: name must start with typed characters")
            
            # Example box
            with st.expander("📘 उदाहरण / Examples"):
                st.markdown("""
                **खोज "र" ले भेट्छ / Search "र" finds (starts with र):**
                - ✅ **राम**, **रमेश**, **राज**
                
                **खोज "राम" ले भेट्छ / Search "राम" finds (starts with राम):**
                - ✅ **राम**, **रामेश**
                
                **खोज "राम" ले भेट्दैन / Search "राम" does NOT find:**
                - ❌ श्रीराम (सुरु श्रीले / starts with श्री)
                - ❌ हरिराम (सुरु हरिले / starts with हरि)
                
                **टिप्स:** टाइप गरेको अक्षरले नाम सुरु हुनुपर्छ।
                """)
            
            search_name = st.text_input("मतदाताको नाम लेख्नुहोस्:", "", key="name_search",
                                       placeholder="उदाहरण: र, रा, राम")
            
            if search_name:
                with st.spinner('खोज्दै... / Searching...'):
                    filtered_df = unicode_prefix_search(df, 'मतदाताको नाम', search_name)
                
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो (खोज: '{search_name}')")
                    st.dataframe(filtered_df[display_columns], use_container_width=True, height=400)
                else:
                    st.warning(f"कुनै पनि मतदाता भेटिएन (खोज: '{search_name}')")
                    st.info("💡 सुझाव: सुरुको अक्षर टाइप गर्नुहोस् जस्तै 'र' वा 'रा'")
            else:
                st.info("खोज्नको लागि मतदाताको नाम लेख्नुहोस्")
        
        elif search_option == "मतदाता नंबरबाट खोज्नुहोस्":
            st.subheader("मतदाता नंबरबाट खोज्नुहोस्")
            search_number = st.text_input("मतदाता नंबर लेख्नुहोस्:", "")
            
            if search_number:
                try:
                    search_num = int(search_number)
                    with st.spinner('खोज्दै... / Searching...'):
                        filtered_df = df[df['मतदाता नं'] == search_num]
                    
                    if not filtered_df.empty:
                        st.success("✅ मतदाता भेटियो")
                        st.dataframe(filtered_df[display_columns], use_container_width=True, height=200)
                    else:
                        st.warning("कुनै पनि मतदाता भेटिएन")
                except ValueError:
                    st.error("कृपया मान्य नंबर लेख्नुहोस्")
            else:
                st.info("खोज्नको लागि मतदाता नंबर लेख्नुहोस्")
        
        elif search_option == "पिता/माताको नामबाट खोज्नुहोस्":
            st.subheader("पिता/माताको नामबाट खोज्नुहोस्")
            st.caption("🔤 उपसर्ग खोज: नाम सुरुको अक्षरले मेल खान्छ / Prefix search: name must start with typed characters")
            
            with st.expander("📘 उदाहरण / Examples"):
                st.markdown("""
                - "ह" → हरि, हेमन्त (ह बाट सुरु)
                - "हर" → हरि, हरिश
                - "हरि" → हरि, हरिकृष्ण
                """)
            
            search_parent = st.text_input("पिता वा माताको नाम लेख्नुहोस्:", "", key="parent_search",
                                         placeholder="उदाहरण: ह, हर, हरि")
            
            if search_parent:
                with st.spinner('खोज्दै... / Searching...'):
                    filtered_df = unicode_prefix_search(df, 'पिता/माताको नाम', search_parent)
                
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो (खोज: '{search_parent}')")
                    st.dataframe(filtered_df[display_columns], use_container_width=True, height=400)
                else:
                    st.warning(f"कुनै पनि मतदाता भेटिएन (खोज: '{search_parent}')")
            else:
                st.info("खोज्नको लागि पिता वा माताको नाम लेख्नुहोस्")
        
        elif search_option == "पति/पत्नीको नामबाट खोज्नुहोस्":
            st.subheader("पति/पत्नीको नामबाट खोज्नुहोस्")
            st.caption("🔤 उपसर्ग खोज: नाम सुरुको अक्षरले मेल खान्छ / Prefix search: name must start with typed characters")
            
            with st.expander("📘 उदाहरण / Examples"):
                st.markdown("""
                - "ग" → गीता, गंगा (ग बाट सुरु)
                - "गी" → गीता, गीतादेवी
                - "गीत" → गीता, गीतादेवी
                """)
            
            search_spouse = st.text_input("पति वा पत्नीको नाम लेख्नुहोस्:", "", key="spouse_search",
                                         placeholder="उदाहरण: ग, गी, गीत")
            
            if search_spouse:
                with st.spinner('खोज्दै... / Searching...'):
                    filtered_df = unicode_prefix_search(df, 'पति/पत्नीको नाम', search_spouse)
                    # Exclude rows where spouse is missing
                    filtered_df = filtered_df[filtered_df['पति/पत्नीको नाम'] != '-']
                
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो (खोज: '{search_spouse}')")
                    st.dataframe(filtered_df[display_columns], use_container_width=True, height=400)
                else:
                    st.warning(f"कुनै पनि मतदाता भेटिएन (खोज: '{search_spouse}')")
            else:
                st.info("खोज्नको लागि पति वा पत्नीको नाम लेख्नुहोस्")
        
        elif search_option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("लिङ्गबाट फिल्टर गर्नुहोस्")
            
            unique_genders = [g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)]
            seen = set()
            gender_options = []
            for x in ["सबै", "पुरुष", "महिला", "अन्य"] + unique_genders:
                if x not in seen:
                    seen.add(x)
                    gender_options.append(x)
            
            selected_gender = st.selectbox("लिङ्ग छान्नुहोस्:", gender_options)
            
            if selected_gender == "सबै":
                filtered_df = df
            else:
                with st.spinner('फिल्टर गर्दै... / Filtering...'):
                    filtered_df = df[df['लिङ्ग'] == selected_gender]
            
            st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
            
            if len(filtered_df) == 0 and selected_gender != "सबै":
                st.info(f"📊 यो डाटामा '{selected_gender}' लिङ्गका मतदाता छैनन्")
            
            st.dataframe(filtered_df[display_columns], use_container_width=True, height=500)
        
        elif search_option == "उमेर दायराबाट खोज्नुहोस्":
            st.subheader("उमेर दायराबाट खोज्नुहोस्")
            
            col1, col2 = st.columns(2)
            
            with col1:
                min_age = st.number_input("न्यूनतम उमेर:", min_value=0, max_value=150, value=18)
            
            with col2:
                max_age = st.number_input("अधिकतम उमेर:", min_value=0, max_value=150, value=100)
            
            with st.spinner('खोज्दै... / Searching...'):
                age_ok = df['उमेर(वर्ष)'].notna()
                in_range = (df['उमेर(वर्ष)'] >= min_age) & (df['उमेर(वर्ष)'] <= max_age)
                filtered_df = df[age_ok & in_range]
            st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो (उमेर: {min_age} - {max_age} वर्ष)")
            st.dataframe(filtered_df[display_columns], use_container_width=True, height=500)
        
        elif search_option == "उन्नत खोज (सबै फिल्टर)":
            st.subheader("🔍 उन्नत खोज - धेरै फिल्टर प्रयोग गर्नुहोस्")
            st.markdown("**तपाईंले चाहानु भएका फिल्टरहरू प्रयोग गर्नुहोस्:**")
            st.caption("🔤 उपसर्ग खोज: नाम सुरुको अक्षरले मेल खान्छ / Unicode-aware prefix search")
            
            # Create filter columns
            col1, col2 = st.columns(2)
            
            with col1:
                # Name filter
                name_filter = st.text_input("मतदाताको नाम:", "", key="adv_name",
                                           placeholder="उदाहरण: र, रा, राम")
                
                # Parent name filter
                parent_filter = st.text_input("पिता/माताको नाम:", "", key="adv_parent",
                                             placeholder="उदाहरण: ह, हर, हरि")
                
                # Spouse name filter
                spouse_filter = st.text_input("पति/पत्नीको नाम:", "", key="adv_spouse",
                                             placeholder="उदाहरण: ग, गी, गीत")
            
            with col2:
                unique_genders_adv = [g for g in df['लिङ्ग'].unique().tolist() if pd.notna(g)]
                seen_adv = set()
                gender_options_adv = []
                for x in ["सबै", "पुरुष", "महिला", "अन्य"] + unique_genders_adv:
                    if x not in seen_adv:
                        seen_adv.add(x)
                        gender_options_adv.append(x)
                gender_filter = st.selectbox("लिङ्ग:", gender_options_adv, key="adv_gender")
                
                # Age range
                age_col1, age_col2 = st.columns(2)
                with age_col1:
                    min_age_filter = st.number_input("न्यूनतम उमेर:", min_value=0, max_value=150, value=0, key="adv_min_age")
                with age_col2:
                    max_age_filter = st.number_input("अधिकतम उमेर:", min_value=0, max_value=150, value=150, key="adv_max_age")
            
            # Apply filters button
            if st.button("🔍 खोज्नुहोस्", type="primary"):
                with st.spinner('खोज्दै... / Searching...'):
                    # Start with full dataset
                    mask = pd.Series([True] * len(df), index=df.index)
                    
                    # Apply name filter (Unicode-aware prefix)
                    if name_filter:
                        name_norm = _normalize_unicode(name_filter)
                        if name_norm:
                            mask &= df['मतदाताको नाम_lower'].str.startswith(name_norm, na=False)
                    
                    # Apply parent filter (Unicode-aware prefix)
                    if parent_filter:
                        parent_norm = _normalize_unicode(parent_filter)
                        if parent_norm:
                            mask &= df['पिता/माताको नाम_lower'].str.startswith(parent_norm, na=False)
                    
                    # Apply spouse filter (Unicode-aware prefix)
                    if spouse_filter:
                        spouse_norm = _normalize_unicode(spouse_filter)
                        if spouse_norm:
                            mask &= (df['पति/पत्नीको नाम'] != '-') & df['पति/पत्नीको नाम_lower'].str.startswith(spouse_norm, na=False)
                    
                    # Apply gender filter
                    if gender_filter != "सबै":
                        mask &= (df['लिङ्ग'] == gender_filter)
                    
                    # Apply age filter (exclude rows with missing age)
                    age_ok = df['उमेर(वर्ष)'].notna()
                    age_in_range = (df['उमेर(वर्ष)'] >= min_age_filter) & (df['उमेर(वर्ष)'] <= max_age_filter)
                    mask &= age_ok & age_in_range

                    filtered_df = df[mask]
                
                # Display results
                st.markdown("---")
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
                    
                    # Show applied filters
                    with st.expander("लागू गरिएका फिल्टरहरू"):
                        if name_filter:
                            st.write(f"- नाम: '{name_filter}' (उपसर्ग)")
                        if parent_filter:
                            st.write(f"- पिता/माता: '{parent_filter}' (उपसर्ग)")
                        if spouse_filter:
                            st.write(f"- पति/पत्नी: '{spouse_filter}' (उपसर्ग)")
                        if gender_filter != "सबै":
                            st.write(f"- लिङ्ग: {gender_filter}")
                        if min_age_filter > 0 or max_age_filter < 150:
                            st.write(f"- उमेर: {min_age_filter} - {max_age_filter} वर्ष")
                    
                    st.dataframe(filtered_df[display_columns], use_container_width=True, height=500)
                else:
                    st.warning("⚠️ कुनै पनि मतदाता भेटिएन। कृपया फिल्टर परिवर्तन गर्नुहोस्।")
                    st.info("💡 सुझाव: सुरुको अक्षर टाइप गर्नुहोस्")
            else:
                st.info("👆 माथिका फिल्टरहरू भर्नुहोस् र 'खोज्नुहोस्' बटन थिच्नुहोस्")
        
        # Statistics in sidebar
        st.sidebar.markdown("---")
        st.sidebar.subheader("तथ्याङ्क")
        st.sidebar.metric("कुल मतदाता", f"{len(df):,}")
        
        if 'लिङ्ग' in df.columns:
            st.sidebar.write("लिङ्ग अनुसार:")
            gender_counts = df['लिङ्ग'].value_counts()
            for gender, count in gender_counts.items():
                st.sidebar.write(f"- {gender}: {count:,}")
        
        if 'उमेर(वर्ष)' in df.columns:
            avg_age = df['उमेर(वर्ष)'].dropna().mean()
            st.sidebar.metric("औसत उमेर", f"{avg_age:.1f} वर्ष" if not pd.isna(avg_age) else "—")

    except FileNotFoundError:
        st.error("⚠️ voterlist.xlsx फाइल भेटिएन! कृपया यो फाइल यही फोल्डरमा राख्नुहोस्।")
    except Exception as e:
        logger.exception("App error")
        st.error(f"त्रुटि: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("**नोट:** यो एक मतदाता सूची खोज प्रणाली हो। सबै डाटा मूल Database फाइलबाट लिइएको छ।")

# Check if user is logged in
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
