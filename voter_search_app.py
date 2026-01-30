import logging
import unicodedata
import pandas as pd
import streamlit as st
import base64
import time
import extra_streamlit_components as stx
from credentials import USERNAME, PASSWORD
import print_logic

# 1. PAGE CONFIG MUST BE FIRST
st.set_page_config(
    page_title="मतदाता सूची खोज प्रणाली",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="auto"
)

# 2. LOGGING SETUP
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# 3. SESSION STATE INITIALIZATION
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# 4. COOKIE CHECK (ONLY RUNS IF NOT LOGGED IN TO PREVENT LOOPS)
if not st.session_state.logged_in:
    cookie_manager = stx.CookieManager()
    time.sleep(0.1) 
    cookies = cookie_manager.get_all()
    if 'voter_auth' in cookies and cookies['voter_auth'] == 'true':
        st.session_state.logged_in = True
        st.rerun()
else:
    # Initialize manager but don't check cookies if already logged in
    cookie_manager = stx.CookieManager()

# --- HELPER FUNCTIONS ---
def _normalize_unicode(s):
    if not isinstance(s, str) or not s: return s
    return unicodedata.normalize("NFC", s.strip().lower())

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except: return None

bell_image_base64 = get_base64_image("bell.png")

# --- CSS ---
st.markdown("""
    <style>
    .main { padding: 0.75rem 1rem; max-width: 100%; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; }
    h1 { color: #c53030; text-align: center; }
    .login-wrapper { display: flex; flex-direction: column; align-items: center; padding: 2rem; }
    .login-card { width: 100%; max-width: 400px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN/LOGOUT ---
def check_login(username, password):
    if not USERNAME and not PASSWORD: return False
    return username == USERNAME and password == PASSWORD

def login_page():
    img_tag = f'<img src="data:image/png;base64,{bell_image_base64}" width="80">' if bell_image_base64 else '🗳️'
    st.markdown(f'<div class="login-wrapper"><div class="login-card">{img_tag}<h3>Voter Search System</h3></div></div>', unsafe_allow_html=True)
    
    with st.form("login"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True):
            if check_login(user, pwd):
                st.session_state.logged_in = True
                cookie_manager.set('voter_auth', 'true', key="set_c")
                st.rerun()
            else:
                st.error("Invalid Credentials")

def logout():
    st.session_state.logged_in = False
    cookie_manager.delete('voter_auth', key="del_c")
    st.rerun()

# --- DATA LOGIC ---
STANDARD_COLUMNS = ['सि.नं.', 'मतदाता नं', 'मतदाताको नाम', 'उमेर(वर्ष)', 'लिङ्ग', 'पति/पत्नीको नाम', 'पिता/माताको नाम']

@st.cache_data
def load_data():
    df = pd.read_excel('voterlist.xlsx')
    # Cleanup columns
    try: df.columns = df.columns.str.strip()
    except: df.columns = [str(c).strip() for c in df.columns]
    
    # Fix numeric
    if 'उमेर(वर्ष)' in df.columns:
        df['उमेर(वर्ष)'] = pd.to_numeric(df['उमेर(वर्ष)'], errors='coerce')
    
    # Create hidden search columns
    for col in ['मतदाताको नाम', 'पिता/माताको नाम', 'पति/पत्नीको नाम']:
        if col in df.columns:
            df[col + '_lower'] = df[col].astype(str).map(lambda s: _normalize_unicode(s))
            if col == 'पति/पत्नीको नाम':
                df[col] = df[col].fillna('-')
                df[col + '_lower'] = df[col + '_lower'].fillna('-')
    return df

def get_display_columns(df):
    cols = [c for c in STANDARD_COLUMNS if c in df.columns]
    for c in df.columns:
        if c not in cols and not c.endswith('_lower'): cols.append(c)
    return cols

def unicode_prefix_search(df, col, term):
    if not term or col + '_lower' not in df.columns: return df
    norm = _normalize_unicode(term)
    return df[df[col + '_lower'].str.startswith(norm, na=False)]

# --- MAIN APP WITH POPUP FIX ---
def main_app():
    st.title("🗳️ मतदाता सूची खोज प्रणाली")
    
    if st.sidebar.button("🚪 Logout"): logout()
    
    try:
        df = load_data()
        disp_cols = get_display_columns(df)
        
        # SEARCH SIDEBAR
        st.sidebar.header("खोज विकल्प")
        option = st.sidebar.selectbox("Select Search:", [
            "सबै डाटा हेर्नुहोस्", "मतदाताको नामबाट खोज्नुहोस्", "मतदाता नंबरबाट खोज्नुहोस्", 
            "पिता/माताको नामबाट खोज्नुहोस्", "पति/पत्नीको नामबाट खोज्नुहोस्",
            "लिङ्गबाट फिल्टर गर्नुहोस्", "उमेर दायराबाट खोज्नुहोस्", "उन्नत खोज (सबै फिल्टर)"
        ], index=7)

        # FILTER LOGIC
        filtered_df = pd.DataFrame()
        table_key = "default"
        
        if option == "सबै डाटा हेर्नुहोस्":
            st.subheader("All Data")
            filtered_df = df
            table_key = "all"
        elif option == "मतदाताको नामबाट खोज्नुहोस्":
            st.subheader("Search by Name")
            q = st.text_input("Name:", key="q_name")
            if q: filtered_df = unicode_prefix_search(df, 'मतदाताको नाम', q)
            table_key = "name"
        elif option == "मतदाता नंबरबाट खोज्नुहोस्":
            st.subheader("Search by Number")
            q = st.text_input("Number:", key="q_num")
            if q: 
                try: filtered_df = df[df['मतदाता नं'] == int(q)]
                except: st.error("Invalid")
            table_key = "num"
        elif option == "पिता/माताको नामबाट खोज्नुहोस्":
            st.subheader("Search by Parent")
            q = st.text_input("Parent:", key="q_par")
            if q: filtered_df = unicode_prefix_search(df, 'पिता/माताको नाम', q)
            table_key = "parent"
        elif option == "पति/पत्नीको नामबाट खोज्नुहोस्":
            st.subheader("Search by Spouse")
            q = st.text_input("Spouse:", key="q_spo")
            if q: 
                filtered_df = unicode_prefix_search(df, 'पति/पत्नीको नाम', q)
                filtered_df = filtered_df[filtered_df['पति/पत्नीको नाम'] != '-']
            table_key = "spouse"
        elif option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("Filter by Gender")
            g = st.selectbox("Gender:", ["सबै"] + list(df['लिङ्ग'].dropna().unique()))
            filtered_df = df if g == "सबै" else df[df['लिङ्ग'] == g]
            table_key = "gender"
        elif option == "उमेर दायराबाट खोज्नुहोस्":
            st.subheader("Filter by Age")
            mn, mx = st.columns(2)
            min_a = mn.number_input("Min", 18)
            max_a = mx.number_input("Max", 100)
            filtered_df = df[(df['उमेर(वर्ष)'] >= min_a) & (df['उमेर(वर्ष)'] <= max_a)]
            table_key = "age"
        elif option == "उन्नत खोज (सबै फिल्टर)":
            st.subheader("Advanced Search")
            c1, c2 = st.columns(2)
            n = c1.text_input("Name", key="a_n")
            p = c1.text_input("Parent", key="a_p")
            s = c1.text_input("Spouse", key="a_s")
            g = c2.selectbox("Gender", ["सबै"] + list(df['लिङ्ग'].unique()), key="a_g")
            amin = c2.number_input("Min Age", 0, key="a_min")
            amax = c2.number_input("Max Age", 120, 120, key="a_max")
            
            if st.button("Search"):
                mask = pd.Series([True]*len(df), index=df.index)
                if n: mask &= df['मतदाताको नाम_lower'].str.startswith(_normalize_unicode(n), na=False)
                if p: mask &= df['पिता/माताको नाम_lower'].str.startswith(_normalize_unicode(p), na=False)
                if s: mask &= df['पति/पत्नीको नाम_lower'].str.startswith(_normalize_unicode(s), na=False)
                if g != "सबै": mask &= (df['लिङ्ग'] == g)
                mask &= (df['उमेर(वर्ष)'] >= amin) & (df['उमेर(वर्ष)'] <= amax)
                filtered_df = df[mask]
            table_key = "adv"

        # DISPLAY TABLE WITH SELECTION
        if not filtered_df.empty:
            st.success(f"Found: {len(filtered_df)}")
            st.info("Click a row to print details / विवरण प्रिन्ट गर्न क्लिक गर्नुहोस्")
            
            # Dynamic Height
            height = max(150, min((len(filtered_df) + 1) * 35, 600))
            
            event = st.dataframe(
                filtered_df[disp_cols],
                use_container_width=True,
                height=height,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key=table_key
            )

            # SAVE SELECTION TO STATE
            if event.selection.rows:
                idx = event.selection.rows[0]
                if idx < len(filtered_df):
                    st.session_state['selected_voter'] = filtered_df.iloc[idx].to_dict()
        
        # STATISTICS SIDEBAR
        st.sidebar.markdown("---")
        st.sidebar.metric("Total", len(df))
        if 'उमेर(वर्ष)' in df.columns:
            st.sidebar.metric("Gen Z", len(df[(df['उमेर(वर्ष)'] >= 18) & (df['उमेर(वर्ष)'] <= 29)]))

    except Exception as e:
        st.error(f"Error: {e}")

    # --- POPUP LOGIC (MUST BE LAST) ---
    if 'selected_voter' in st.session_state:
        # Use try-except to prevent crash if popup logic fails
        try:
            print_logic.show_voter_popup(st.session_state['selected_voter'])
        except Exception as e:
            # If popup fails, clear state so app doesn't break
            st.error(f"Popup error: {e}")
            del st.session_state['selected_voter']

# EXECUTE
if not st.session_state.logged_in:
    login_page()
else:
    main_app()