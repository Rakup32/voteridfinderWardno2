import pandas as pd
import streamlit as st
import base64
import re
from credentials import USERNAME, PASSWORD

# Set page configuration
st.set_page_config(
    page_title="मतदाता सूची खोज प्रणाली",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to convert image to base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Get base64 encoded bell image
bell_image_base64 = get_base64_image("bell.png")

# Custom CSS for better styling and mobile responsiveness
st.markdown(f"""
    <style>
    .main {{
        padding: 0rem 1rem;
    }}
    .stDataFrame {{
        border: 2px solid #f0f2f6;
        border-radius: 5px;
    }}
    h1 {{
        color: #FF4B4B;
        text-align: center;
        padding: 1rem 0;
    }}
    .search-box {{
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }}
    
    /* Mobile Responsive Styles */
    @media screen and (max-width: 768px) {{
        .main {{
            padding: 0.5rem;
        }}
        h1 {{
            font-size: 1.5rem !important;
        }}
        h2 {{
            font-size: 1.2rem !important;
        }}
        h3 {{
            font-size: 1rem !important;
        }}
        .stDataFrame {{
            font-size: 0.8rem;
        }}
        [data-testid="stSidebar"] {{
            min-width: 250px;
        }}
    }}
    
    /* Clean Login Page Styling */
    .login-container {{
        max-width: 450px;
        margin: 3rem auto;
        padding: 2rem;
        text-align: center;
    }}
    
    .bell-icon {{
        width: 120px;
        height: 120px;
        margin: 0 auto 2rem;
        animation: swing 2s ease-in-out infinite;
    }}
    
    @keyframes swing {{
        0%, 100% {{
            transform: rotate(0deg);
        }}
        25% {{
            transform: rotate(10deg);
        }}
        75% {{
            transform: rotate(-10deg);
        }}
    }}
    
    .login-title {{
        color: #2d3748;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }}
    
    .login-subtitle {{
        color: #FF4B4B;
        font-size: 1.3rem;
        margin-bottom: 0.3rem;
        font-weight: 600;
    }}
    
    .login-subtitle-en {{
        color: #718096;
        font-size: 0.95rem;
        margin-bottom: 2.5rem;
    }}
    
    .divider {{
        height: 2px;
        background: linear-gradient(to right, transparent, #FF4B4B, transparent);
        margin: 1.5rem 0;
    }}
    
    @media screen and (max-width: 768px) {{
        .login-container {{
            padding: 1.5rem;
            margin: 2rem auto;
        }}
        .bell-icon {{
            width: 90px;
            height: 90px;
        }}
        .login-title {{
            font-size: 1.5rem;
        }}
        .login-subtitle {{
            font-size: 1.1rem;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Login function
def check_login(username, password):
    return username == USERNAME and password == PASSWORD

# Login page
def login_page():
    # Create centered container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Display bell icon
    if bell_image_base64:
        st.markdown(f'''
            <div class="bell-icon">
                <img src="data:image/png;base64,{bell_image_base64}" style="width: 100%; height: 100%;" />
            </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="bell-icon">🔔</div>', unsafe_allow_html=True)
    
    # Title
    st.markdown('<div class="login-title">🔐 सुरक्षित प्रवेश</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">मतदाता सूची खोज प्रणाली</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle-en">Voter List Search System</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("👤 प्रयोगकर्ता नाम / Username", key="username", placeholder="Enter your username")
        password = st.text_input("🔒 पासवर्ड / Password", type="password", key="password", placeholder="Enter your password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        submit = st.form_submit_button("🔓 लगइन गर्नुहोस् / Login", use_container_width=True)
        
        if submit:
            if check_login(username, password):
                st.session_state.logged_in = True
                st.success("✅ लगइन सफल भयो! / Login Successful!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ गलत प्रयोगकर्ता नाम वा पासवर्ड / Invalid Credentials")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Logout function
def logout():
    st.session_state.logged_in = False
    st.rerun()

# Optimized data loading with preprocessing
@st.cache_data
def load_data():
    df = pd.read_excel('voterlist.xlsx')
    
    # Create lowercase versions for case-insensitive search
    df['मतदाताको नाम_lower'] = df['मतदाताको नाम'].str.lower()
    df['पिता/माताको नाम_lower'] = df['पिता/माताको नाम'].str.lower()
    df['पति/पत्नीको नाम_lower'] = df['पति/पत्नीको नाम'].str.lower()
    
    # Fill NaN values for faster filtering
    df['पति/पत्नीको नाम'] = df['पति/पत्नीको नाम'].fillna('-')
    df['पति/पत्नीको नाम_lower'] = df['पति/पत्नीको नाम_lower'].fillna('-')
    
    return df

# Ordered substring search function
def ordered_substring_search(df, column, search_term):
    """
    Ordered substring search - matches characters in exact sequence.
    
    Examples:
    - Search "रम" matches "राम", "रमेश"
    - Search "रम" does NOT match "मर", "अमर"
    - Characters must appear in the exact order typed
    """
    if not search_term:
        return df
    
    # Convert to lowercase for case-insensitive matching
    search_lower = search_term.lower().strip()
    lower_col = column + '_lower'
    
    # Escape special regex characters except spaces
    search_escaped = re.escape(search_lower)
    
    # Create regex pattern: each character can have any characters between them
    # But they must appear in order
    # Example: "रम" becomes "र.*म" which matches "राम", "रमेश" but not "मर"
    pattern = '.*'.join(search_escaped)
    
    # Apply the pattern - matches if characters appear in order
    mask = df[lower_col].str.contains(pattern, na=False, regex=True, case=False)
    
    return df[mask]

# Main app (only shown after login)
def main_app():
    # Title
    st.title("🗳️ मतदाता सूची खोज प्रणाली")
    st.markdown("**Voter List Search System**")
    
    # Logout button in sidebar
    with st.sidebar:
        if st.button("🚪 Logout / बाहिर निस्कनुहोस्", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    try:
        # Load data with spinner
        with st.spinner('डाटा लोड गर्दै... / Loading data...'):
            df = load_data()
        
        # Display columns to show (exclude lowercase helper columns)
        display_columns = ['सि.नं.', 'मतदाता नं', 'मतदाताको नाम', 'उमेर(वर्ष)', 'लिङ्ग', 'पति/पत्नीको नाम', 'पिता/माताको नाम']
        
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
            st.caption("🔤 क्रमबद्ध खोज: वर्णहरू क्रमैसँग मेल खान्छ / Ordered search: characters must match in sequence")
            
            # Example box
            with st.expander("📘 उदाहरण / Examples"):
                st.markdown("""
                **खोज "रम" ले भेट्छ / Search "रम" finds:**
                - ✅ **राम** (र-आ-म)
                - ✅ **रमेश** (र-म-े-श)
                - ✅ **श्रीराम** (श्री-रा-म)
                
                **खोज "रम" ले भेट्दैन / Search "रम" does NOT find:**
                - ❌ मर (क्रम फरक / wrong order)
                - ❌ अमर (र पहिले छैन / र not first)
                
                **टिप्स:**
                - "र" = र बाट सुरु हुने सबै नाम
                - "रा" = रा बाट सुरु हुने नाम
                - "राम" = राम भएका नाम
                """)
            
            search_name = st.text_input("मतदाताको नाम लेख्नुहोस्:", "", key="name_search", 
                                       placeholder="उदाहरण: र, रा, राम")
            
            if search_name:
                with st.spinner('खोज्दै... / Searching...'):
                    filtered_df = ordered_substring_search(df, 'मतदाताको नाम', search_name)
                
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो (खोज: '{search_name}')")
                    st.dataframe(filtered_df[display_columns], use_container_width=True, height=400)
                else:
                    st.warning(f"कुनै पनि मतदाता भेटिएन (खोज: '{search_name}')")
                    st.info("💡 सुझाव: कम वर्ण प्रयोग गरी खोज्नुहोस् जस्तै 'र' वा 'रा'")
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
            st.caption("🔤 क्रमबद्ध खोज: वर्णहरू क्रमैसँग मेल खान्छ / Ordered search: characters must match in sequence")
            
            with st.expander("📘 उदाहरण / Examples"):
                st.markdown("""
                - "ह" → हरि, हेमन्त, महेश
                - "हर" → हरि, हरिश
                - "हरि" → हरि, हरिकृष्ण
                """)
            
            search_parent = st.text_input("पिता वा माताको नाम लेख्नुहोस्:", "", key="parent_search",
                                         placeholder="उदाहरण: ह, हर, हरि")
            
            if search_parent:
                with st.spinner('खोज्दै... / Searching...'):
                    filtered_df = ordered_substring_search(df, 'पिता/माताको नाम', search_parent)
                
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो (खोज: '{search_parent}')")
                    st.dataframe(filtered_df[display_columns], use_container_width=True, height=400)
                else:
                    st.warning(f"कुनै पनि मतदाता भेटिएन (खोज: '{search_parent}')")
            else:
                st.info("खोज्नको लागि पिता वा माताको नाम लेख्नुहोस्")
        
        elif search_option == "पति/पत्नीको नामबाट खोज्नुहोस्":
            st.subheader("पति/पत्नीको नामबाट खोज्नुहोस्")
            st.caption("🔤 क्रमबद्ध खोज: वर्णहरू क्रमैसँग मेल खान्छ / Ordered search: characters must match in sequence")
            
            with st.expander("📘 उदाहरण / Examples"):
                st.markdown("""
                - "ग" → गीता, गंगा, मनगरी
                - "गी" → गीता, गीतादेवी
                - "गीत" → गीता, गीतादेवी
                """)
            
            search_spouse = st.text_input("पति वा पत्नीको नाम लेख्नुहोस्:", "", key="spouse_search",
                                         placeholder="उदाहरण: ग, गी, गीत")
            
            if search_spouse:
                with st.spinner('खोज्दै... / Searching...'):
                    # Filter out NaN and '-' values first
                    search_lower = search_spouse.lower().strip()
                    search_escaped = re.escape(search_lower)
                    pattern = '.*'.join(search_escaped)
                    
                    mask = (df['पति/पत्नीको नाम'] != '-') & df['पति/पत्नीको नाम_lower'].str.contains(pattern, na=False, regex=True, case=False)
                    filtered_df = df[mask]
                
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो (खोज: '{search_spouse}')")
                    st.dataframe(filtered_df[display_columns], use_container_width=True, height=400)
                else:
                    st.warning(f"कुनै पनि मतदाता भेटिएन (खोज: '{search_spouse}')")
            else:
                st.info("खोज्नको लागि पति वा पत्नीको नाम लेख्नुहोस्")
        
        elif search_option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("लिङ्गबाट फिल्टर गर्नुहोस्")
            
            # Get unique gender values from data
            unique_genders = df['लिङ्ग'].unique().tolist()
            
            # Add common gender options if not in data
            gender_options = ["सबै"]
            if "पुरुष" not in unique_genders:
                gender_options.append("पुरुष")
            if "महिला" not in unique_genders:
                gender_options.append("महिला")
            if "अन्य" not in unique_genders:
                gender_options.append("अन्य")
            
            # Add existing unique values
            gender_options.extend(unique_genders)
            
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
                filtered_df = df[(df['उमेर(वर्ष)'] >= min_age) & (df['उमेर(वर्ष)'] <= max_age)]
            
            st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो (उमेर: {min_age} - {max_age} वर्ष)")
            st.dataframe(filtered_df[display_columns], use_container_width=True, height=500)
        
        elif search_option == "उन्नत खोज (सबै फिल्टर)":
            st.subheader("🔍 उन्नत खोज - धेरै फिल्टर प्रयोग गर्नुहोस्")
            st.markdown("**तपाईंले चाहानु भएका फिल्टरहरू प्रयोग गर्नुहोस्:**")
            st.caption("🔤 क्रमबद्ध खोज: वर्णहरू क्रमैसँग मेल खान्छ / Ordered search")
            
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
                # Gender filter
                unique_genders = df['लिङ्ग'].unique().tolist()
                gender_options = ["सबै", "पुरुष", "महिला", "अन्य"]
                for g in unique_genders:
                    if g not in gender_options:
                        gender_options.append(g)
                
                gender_filter = st.selectbox("लिङ्ग:", gender_options, key="adv_gender")
                
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
                    
                    # Apply name filter (ordered substring)
                    if name_filter:
                        name_lower = name_filter.lower().strip()
                        name_escaped = re.escape(name_lower)
                        name_pattern = '.*'.join(name_escaped)
                        mask &= df['मतदाताको नाम_lower'].str.contains(name_pattern, na=False, regex=True, case=False)
                    
                    # Apply parent filter (ordered substring)
                    if parent_filter:
                        parent_lower = parent_filter.lower().strip()
                        parent_escaped = re.escape(parent_lower)
                        parent_pattern = '.*'.join(parent_escaped)
                        mask &= df['पिता/माताको नाम_lower'].str.contains(parent_pattern, na=False, regex=True, case=False)
                    
                    # Apply spouse filter (ordered substring)
                    if spouse_filter:
                        spouse_lower = spouse_filter.lower().strip()
                        spouse_escaped = re.escape(spouse_lower)
                        spouse_pattern = '.*'.join(spouse_escaped)
                        mask &= (df['पति/पत्नीको नाम'] != '-') & df['पति/पत्नीको नाम_lower'].str.contains(spouse_pattern, na=False, regex=True, case=False)
                    
                    # Apply gender filter
                    if gender_filter != "सबै":
                        mask &= (df['लिङ्ग'] == gender_filter)
                    
                    # Apply age filter
                    mask &= (df['उमेर(वर्ष)'] >= min_age_filter) & (df['उमेर(वर्ष)'] <= max_age_filter)
                    
                    filtered_df = df[mask]
                
                # Display results
                st.markdown("---")
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df):,} मतदाता भेटियो")
                    
                    # Show applied filters
                    with st.expander("लागू गरिएका फिल्टरहरू"):
                        if name_filter:
                            st.write(f"- नाम: '{name_filter}' (क्रमबद्ध)")
                        if parent_filter:
                            st.write(f"- पिता/माता: '{parent_filter}' (क्रमबद्ध)")
                        if spouse_filter:
                            st.write(f"- पति/पत्नी: '{spouse_filter}' (क्रमबद्ध)")
                        if gender_filter != "सबै":
                            st.write(f"- लिङ्ग: {gender_filter}")
                        if min_age_filter > 0 or max_age_filter < 150:
                            st.write(f"- उमेर: {min_age_filter} - {max_age_filter} वर्ष")
                    
                    st.dataframe(filtered_df[display_columns], use_container_width=True, height=500)
                else:
                    st.warning("⚠️ कुनै पनि मतदाता भेटिएन। कृपया फिल्टर परिवर्तन गर्नुहोस्।")
                    st.info("💡 सुझाव: कम वर्ण प्रयोग गरी खोज्नुहोस्")
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
            st.sidebar.metric("औसत उमेर", f"{df['उमेर(वर्ष)'].mean():.1f} वर्ष")

    except FileNotFoundError:
        st.error("⚠️ voterlist.xlsx फाइल भेटिएन! कृपया यो फाइल यही फोल्डरमा राख्नुहोस्।")
    except Exception as e:
        st.error(f"त्रुटि: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("**नोट:** यो एक मतदाता सूची खोज प्रणाली हो। सबै डाटा मूल Excel फाइलबाट लिइएको छ।")

# Check if user is logged in
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
