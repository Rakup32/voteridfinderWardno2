import logging
import unicodedata
import pandas as pd
import streamlit as st
import base64
import time
import extra_streamlit_components as stx
from credentials import USERNAME, PASSWORD
import print_logic  # Must exist in the same folder!

def _normalize_unicode(s):
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

# --- FIXED COOKIE MANAGER (NO LOOP) ---
cookie_manager = stx.CookieManager()

# Initialize session state for login if not present
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Check cookies ONLY if we are not already logged in
if not st.session_state.logged_in:
    time.sleep(0.2) # Short wait for cookies to load
    cookies = cookie_manager.get_all()
    if 'voter_auth' in cookies and cookies['voter_auth'] == 'true':
        st.session_state.logged_in = True
        # Do NOT rerun here, just let the script continue
# ---------------------------------------

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError) as e:
        return None

bell_image_base64 = get_base64_image("bell.png")

st.markdown("""
    <style>
    .main { padding: 0.75rem 1rem; max-width: 100%; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    h1 { color: #c53030; text-align: center; padding: 0.75rem 0; word-break: break-word; }
    .login-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1rem; }
    .login-card { width: 100%; max-width: 560px; padding: 2rem 1.75rem 0; text-align: center; margin: 0 auto; }
    .login-logo { width: 80px; height: 80px; margin: 0 auto 1rem; border-radius: 14px; background: #f7fafc; }
    .login-logo img { width: 100%; height: 100%; object-fit: contain; }
    .login-title { color: #2d3748; font-size: 1.25rem; font-weight: 700; margin-bottom: 0.3rem; }
    </style>
    """, unsafe_allow_html=True)

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
    st.markdown(f"""
    <div class="login-wrapper">
    <div class="login-card">
        {logo_html}
        <div class="login-title">सुरक्षित प्रवेश</div>
        <div>Voter List Search System</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if check_login(username, password):
                st.session_state.logged_in = True
                cookie_manager.set('voter_auth', 'true', expires_at=None, key="set_auth")
                st.success("Login Success!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Invalid Credentials")

def logout():
    st.session_state.logged_in = False
    cookie_manager.delete('voter_auth', key="del_auth")
    st.rerun()

# --- DATA LOADING ---
STANDARD_COLUMNS = ['सि.नं.', 'मतदाता नं', 'मतदाताको नाम', 'उमेर(वर्ष)', 'लिङ्ग', 'पति/पत्नीको नाम', 'पिता/माताको नाम']

@st.cache_data
def load_data():
    df = pd.read_excel('voterlist.xlsx')
    try:
        df.columns = df.columns.str.strip()
    except AttributeError:
        df.columns = [str(c).strip() for c in df.columns]

    if 'उमेर(वर्ष)' in df.columns:
        df['उमेर(वर्ष)'] = pd.to_numeric(df['उमेर(वर्ष)'], errors='coerce')
    
    # Precompute lowercase columns for search
    for col in ['मतदाताको नाम', 'पिता/माताको नाम', 'पति/पत्नीको नाम']:
        if col in df.columns:
            df[col + '_lower'] = df[col].astype(str).map(lambda s: _normalize_unicode(s))
            if col == 'पति/पत्नीको नाम':
                df[col] = df[col].fillna('-')
                df[col + '_lower'] = df[col + '_lower'].fillna('-')
    return df

def get_display_columns(df):
    final_cols = [c for c in STANDARD_COLUMNS if c in df.columns]
    for c in df.columns:
        if c not in final_cols and not c.endswith('_lower'):
            final_cols.append(c)
    return final_cols

def unicode_prefix_search(df, column, search_term):
    if not search_term or column not in df.columns: return df
    normalized = _normalize_unicode(search_term)
    lower_col = column + "_lower"
    if lower_col not in df.columns: return df
    return df[df[lower_col].str.startswith(normalized, na=False)]

# --- TABLE FUNCTION ---
def show_results_table(data, columns, table_key):
    if data.empty: return
    
    # Calculate height
    height = max(150, min((len(data) + 1) * 35, 800))
    
    st.info("👇 विवरण हेर्न तलको तालिकाको पङ्क्तिमा क्लिक गर्नुहोस् (Click row for details)")
    
    # RENDER TABLE
    event = st.dataframe(
        data[columns],
        use_container_width=True,
        height=height,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=table_key
    )

    # CAPTURE SELECTION IMMEDIATELY
    if event.selection.rows:
        idx = event.selection.rows[0]
        # Only update if valid index
        if idx < len(data):
            # Save the ACTUAL data row to session state
            st.session_state['selected_voter_data'] = data.iloc[idx].to_dict()

def main_app():
    st.title("🗳️ मतदाता सूची खोज प्रणाली")
    
    with st.sidebar:
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    st.markdown("---")
    
    try:
        df = load_data()
        display_columns = get_display_columns(df)
        
        # Sidebar
        st.sidebar.header("खोज विकल्प")
        search_option = st.sidebar.selectbox("खोज प्रकार:", [
            "सबै डाटा हेर्नुहोस्", "मतदाताको नामबाट खोज्नुहोस्", "मतदाता नंबरबाट खोज्नुहोस्", 
            "पिता/माताको नामबाट खोज्नुहोस्", "पति/पत्नीको नामबाट खोज्नुहोस्",
            "लिङ्गबाट फिल्टर गर्नुहोस्", "उमेर दायराबाट खोज्नुहोस्", "उन्नत खोज (सबै फिल्टर)"
        ], index=7)

        # Logic to determine filtered_df
        filtered_df = pd.DataFrame() # Empty by default
        show_table = False
        table_id = "default"

        if search_option == "सबै डाटा हेर्नुहोस्":
            st.subheader("सम्पूर्ण मतदाता सूची")
            filtered_df = df
            show_table = True
            table_id = "t_all"

        elif search_option == "मतदाताको नामबाट खोज्नुहोस्":
            st.subheader("नामबाट खोज्नुहोस्")
            search_name = st.text_input("नाम:", key="s_name")
            if search_name:
                filtered_df = unicode_prefix_search(df, 'मतदाताको नाम', search_name)
                show_table = True
                table_id = "t_name"

        elif search_option == "मतदाता नंबरबाट खोज्नुहोस्":
            st.subheader("नंबरबाट खोज्नुहोस्")
            search_num = st.text_input("नंबर:", key="s_num")
            if search_num:
                try:
                    filtered_df = df[df['मतदाता नं'] == int(search_num)]
                    show_table = True
                    table_id = "t_num"
                except: st.error("Invalid Number")

        elif search_option == "पिता/माताको नामबाट खोज्नुहोस्":
            st.subheader("पिता/माताको नामबाट खोज्नुहोस्")
            search_p = st.text_input("नाम:", key="s_parent")
            if search_p:
                filtered_df = unicode_prefix_search(df, 'पिता/माताको नाम', search_p)
                show_table = True
                table_id = "t_parent"

        elif search_option == "पति/पत्नीको नामबाट खोज्नुहोस्":
            st.subheader("पति/पत्नीको नामबाट खोज्नुहोस्")
            search_s = st.text_input("नाम:", key="s_spouse")
            if search_s:
                filtered_df = unicode_prefix_search(df, 'पति/पत्नीको नाम', search_s)
                filtered_df = filtered_df[filtered_df['पति/पत्नीको नाम'] != '-']
                show_table = True
                table_id = "t_spouse"

        elif search_option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("लिङ्गबाट फिल्टर गर्नुहोस्")
            genders = ["सबै"] + list(df['लिङ्ग'].dropna().unique())
            sel_gen = st.selectbox("Select:", genders)
            if sel_gen == "सबै": filtered_df = df
            else: filtered_df = df[df['लिङ्ग'] == sel_gen]
            show_table = True
            table_id = "t_gen"

        elif search_option == "उमेर दायराबाट खोज्नुहोस्":
            st.subheader("उमेर")
            c1,c2 = st.columns(2)
            min_a = c1.number_input("Min:", 18)
            max_a = c2.number_input("Max:", 100)
            filtered_df = df[(df['उमेर(वर्ष)'] >= min_a) & (df['उमेर(वर्ष)'] <= max_a)]
            show_table = True
            table_id = "t_age"

        elif search_option == "उन्नत खोज (सबै फिल्टर)":
            st.subheader("🔍 उन्नत खोज")
            c1, c2 = st.columns(2)
            name_f = c1.text_input("Name:", key="adv_n")
            parent_f = c1.text_input("Parent:", key="adv_p")
            spouse_f = c1.text_input("Spouse:", key="adv_s")
            gender_f = c2.selectbox("Gender:", ["सबै"] + list(df['लिङ्ग'].unique()), key="adv_g")
            min_af = c2.number_input("Min Age:", 0, key="adv_amin")
            max_af = c2.number_input("Max Age:", 120, 120, key="adv_amax")
            
            if st.button("Search"):
                mask = pd.Series([True]*len(df), index=df.index)
                if name_f: mask &= df['मतदाताको नाम_lower'].str.startswith(_normalize_unicode(name_f), na=False)
                if parent_f: mask &= df['पिता/माताको नाम_lower'].str.startswith(_normalize_unicode(parent_f), na=False)
                if spouse_f: mask &= df['पति/पत्नीको नाम_lower'].str.startswith(_normalize_unicode(spouse_f), na=False)
                if gender_f != "सबै": mask &= (df['लिङ्ग'] == gender_f)
                mask &= (df['उमेर(वर्ष)'] >= min_af) & (df['उमेर(वर्ष)'] <= max_af)
                filtered_df = df[mask]
                show_table = True
                table_id = "t_adv"

        # --- DISPLAY TABLE ---
        if show_table:
            if not filtered_df.empty:
                st.success(f"Found: {len(filtered_df)}")
                # This function updates session state if clicked
                show_results_table(filtered_df, display_columns, table_id)
            else:
                st.warning("No data found")

        # --- STATISTICS ---
        st.sidebar.markdown("---")
        st.sidebar.metric("Total", len(df))
        if 'उमेर(वर्ष)' in df.columns:
            st.sidebar.metric("Gen Z", len(df[(df['उमेर(वर्ष)'] >= 18) & (df['उमेर(वर्ष)'] <= 29)]))

    except Exception as e:
        st.error(f"Error: {e}")

    # --- POPUP TRIGGER (CRITICAL: MUST BE AT END OF MAIN APP) ---
    # This checks if a voter was selected during the table interaction above
    if 'selected_voter_data' in st.session_state:
        try:
            # We must convert dict back to series or access as dict
            # show_voter_popup expects a row-like object
            print_logic.show_voter_popup(st.session_state['selected_voter_data'])
        except Exception as e:
            st.error(f"Popup failed: {e}")
            # Clear state if it fails to prevent loop
            del st.session_state['selected_voter_data']

if not st.session_state.logged_in:
    login_page()
else:
    main_app()