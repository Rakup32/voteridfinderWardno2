import pandas as pd
import streamlit as st
from credentials import USERNAME, PASSWORD

# Set page configuration
st.set_page_config(
    page_title="मतदाता सूची खोज प्रणाली",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling and mobile responsiveness
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stDataFrame {
        border: 2px solid #f0f2f6;
        border-radius: 5px;
    }
    h1 {
        color: #FF4B4B;
        text-align: center;
        padding: 1rem 0;
    }
    .search-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Mobile Responsive Styles */
    @media screen and (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.2rem !important;
        }
        h3 {
            font-size: 1rem !important;
        }
        .stDataFrame {
            font-size: 0.8rem;
        }
        [data-testid="stSidebar"] {
            min-width: 250px;
        }
    }
    
    /* Login Form Styling */
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        background: #f0f2f6;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    @media screen and (max-width: 768px) {
        .login-container {
            margin: 50px auto;
            padding: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Initialize default search option
if 'default_loaded' not in st.session_state:
    st.session_state.default_loaded = False

# Login function
def check_login(username, password):
    return username == USERNAME and password == PASSWORD

# Login page
def login_page():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.title("🔐 Login")
    st.markdown("### मतदाता सूची खोज प्रणाली")
    st.markdown("**Voter List Search System**")
    st.markdown("---")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username / प्रयोगकर्ता नाम:", key="username")
        password = st.text_input("Password / पासवर्ड:", type="password", key="password")
        submit = st.form_submit_button("🔓 Login / लगइन गर्नुहोस्", use_container_width=True)
        
        if submit:
            if check_login(username, password):
                st.session_state.logged_in = True
                st.success("✅ Login successful! / लगइन सफल भयो!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password / गलत प्रयोगकर्ता नाम वा पासवर्ड")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.default_loaded = False
    st.rerun()

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('voterlist.xlsx')
    return df

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
        df = load_data()
        
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
            st.dataframe(df, use_container_width=True, height=600)
            st.info(f"कुल मतदाता संख्या: {len(df)}")
        
        elif search_option == "मतदाताको नामबाट खोज्नुहोस्":
            st.subheader("मतदाताको नामबाट खोज्नुहोस्")
            search_name = st.text_input("मतदाताको नाम लेख्नुहोस्:", "", key="name_search")
            
            if search_name:
                filtered_df = df[df['मतदाताको नाम'].str.contains(search_name, case=False, na=False)]
                
                if not filtered_df.empty:
                    st.success(f"{len(filtered_df)} मतदाता भेटियो")
                    st.dataframe(filtered_df, use_container_width=True, height=400)
                else:
                    st.warning("कुनै पनि मतदाता भेटिएन")
            else:
                st.info("खोज्नको लागि मतदाताको नाम लेख्नुहोस्")
        
        elif search_option == "मतदाता नंबरबाट खोज्नुहोस्":
            st.subheader("मतदाता नंबरबाट खोज्नुहोस्")
            search_number = st.text_input("मतदाता नंबर लेख्नुहोस्:", "")
            
            if search_number:
                try:
                    search_num = int(search_number)
                    filtered_df = df[df['मतदाता नं'] == search_num]
                    
                    if not filtered_df.empty:
                        st.success("मतदाता भेटियो")
                        st.dataframe(filtered_df, use_container_width=True, height=200)
                    else:
                        st.warning("कुनै पनि मतदाता भेटिएन")
                except ValueError:
                    st.error("कृपया मान्य नंबर लेख्नुहोस्")
            else:
                st.info("खोज्नको लागि मतदाता नंबर लेख्नुहोस्")
        
        elif search_option == "पिता/माताको नामबाट खोज्नुहोस्":
            st.subheader("पिता/माताको नामबाट खोज्नुहोस्")
            search_parent = st.text_input("पिता वा माताको नाम लेख्नुहोस्:", "", key="parent_search")
            
            if search_parent:
                filtered_df = df[df['पिता/माताको नाम'].str.contains(search_parent, case=False, na=False)]
                
                if not filtered_df.empty:
                    st.success(f"{len(filtered_df)} मतदाता भेटियो")
                    st.dataframe(filtered_df, use_container_width=True, height=400)
                else:
                    st.warning("कुनै पनि मतदाता भेटिएन")
            else:
                st.info("खोज्नको लागि पिता वा माताको नाम लेख्नुहोस्")
        
        elif search_option == "पति/पत्नीको नामबाट खोज्नुहोस्":
            st.subheader("पति/पत्नीको नामबाट खोज्नुहोस्")
            search_spouse = st.text_input("पति वा पत्नीको नाम लेख्नुहोस्:", "", key="spouse_search")
            
            if search_spouse:
                # Filter out NaN and '-' values
                filtered_df = df[
                    (df['पति/पत्नीको नाम'].notna()) & 
                    (df['पति/पत्नीको नाम'] != '-') &
                    (df['पति/पत्नीको नाम'].str.contains(search_spouse, case=False, na=False))
                ]
                
                if not filtered_df.empty:
                    st.success(f"{len(filtered_df)} मतदाता भेटियो")
                    st.dataframe(filtered_df, use_container_width=True, height=400)
                else:
                    st.warning("कुनै पनि मतदाता भेटिएन")
            else:
                st.info("खोज्नको लागि पति वा पत्नीको नाम लेख्नुहोस्")
        
        elif search_option == "लिङ्गबाट फिल्टर गर्नुहोस्":
            st.subheader("लिङ्गबाट फिल्टर गर्नुहोस्")
            
            unique_genders = df['लिङ्ग'].unique().tolist()
            selected_gender = st.selectbox("लिङ्ग छान्नुहोस्:", ["सबै"] + unique_genders)
            
            if selected_gender == "सबै":
                filtered_df = df
            else:
                filtered_df = df[df['लिङ्ग'] == selected_gender]
            
            st.success(f"{len(filtered_df)} मतदाता भेटियो")
            st.dataframe(filtered_df, use_container_width=True, height=500)
        
        elif search_option == "उमेर दायराबाट खोज्नुहोस्":
            st.subheader("उमेर दायराबाट खोज्नुहोस्")
            
            col1, col2 = st.columns(2)
            
            with col1:
                min_age = st.number_input("न्यूनतम उमेर:", min_value=0, max_value=150, value=18)
            
            with col2:
                max_age = st.number_input("अधिकतम उमेर:", min_value=0, max_value=150, value=100)
            
            filtered_df = df[(df['उमेर(वर्ष)'] >= min_age) & (df['उमेर(वर्ष)'] <= max_age)]
            
            st.success(f"{len(filtered_df)} मतदाता भेटियो (उमेर: {min_age} - {max_age} वर्ष)")
            st.dataframe(filtered_df, use_container_width=True, height=500)
        
        elif search_option == "उन्नत खोज (सबै फिल्टर)":
            st.subheader("🔍 उन्नत खोज - धेरै फिल्टर प्रयोग गर्नुहोस्")
            st.markdown("**तपाईंले चाहानु भएका फिल्टरहरू प्रयोग गर्नुहोस्:**")
            
            # Create filter columns
            col1, col2 = st.columns(2)
            
            with col1:
                # Name filter
                name_filter = st.text_input("मतदाताको नाम:", "", key="adv_name")
                
                # Parent name filter
                parent_filter = st.text_input("पिता/माताको नाम:", "", key="adv_parent")
                
                # Spouse name filter
                spouse_filter = st.text_input("पति/पत्नीको नाम:", "", key="adv_spouse")
            
            with col2:
                # Gender filter
                unique_genders = df['लिङ्ग'].unique().tolist()
                gender_filter = st.selectbox("लिङ्ग:", ["सबै"] + unique_genders, key="adv_gender")
                
                # Age range
                age_col1, age_col2 = st.columns(2)
                with age_col1:
                    min_age_filter = st.number_input("न्यूनतम उमेर:", min_value=0, max_value=150, value=0, key="adv_min_age")
                with age_col2:
                    max_age_filter = st.number_input("अधिकतम उमेर:", min_value=0, max_value=150, value=150, key="adv_max_age")
            
            # Apply filters button
            if st.button("🔍 खोज्नुहोस्", type="primary"):
                filtered_df = df.copy()
                
                # Apply name filter
                if name_filter:
                    filtered_df = filtered_df[filtered_df['मतदाताको नाम'].str.contains(name_filter, case=False, na=False)]
                
                # Apply parent filter
                if parent_filter:
                    filtered_df = filtered_df[filtered_df['पिता/माताको नाम'].str.contains(parent_filter, case=False, na=False)]
                
                # Apply spouse filter
                if spouse_filter:
                    filtered_df = filtered_df[
                        (filtered_df['पति/पत्नीको नाम'].notna()) & 
                        (filtered_df['पति/पत्नीको नाम'] != '-') &
                        (filtered_df['पति/पत्नीको नाम'].str.contains(spouse_filter, case=False, na=False))
                    ]
                
                # Apply gender filter
                if gender_filter != "सबै":
                    filtered_df = filtered_df[filtered_df['लिङ्ग'] == gender_filter]
                
                # Apply age filter
                filtered_df = filtered_df[(filtered_df['उमेर(वर्ष)'] >= min_age_filter) & (filtered_df['उमेर(वर्ष)'] <= max_age_filter)]
                
                # Display results
                st.markdown("---")
                if not filtered_df.empty:
                    st.success(f"✅ {len(filtered_df)} मतदाता भेटियो")
                    
                    # Show applied filters
                    with st.expander("लागू गरिएका फिल्टरहरू"):
                        if name_filter:
                            st.write(f"- नाम: {name_filter}")
                        if parent_filter:
                            st.write(f"- पिता/माता: {parent_filter}")
                        if spouse_filter:
                            st.write(f"- पति/पत्नी: {spouse_filter}")
                        if gender_filter != "सबै":
                            st.write(f"- लिङ्ग: {gender_filter}")
                        if min_age_filter > 0 or max_age_filter < 150:
                            st.write(f"- उमेर: {min_age_filter} - {max_age_filter} वर्ष")
                    
                    st.dataframe(filtered_df, use_container_width=True, height=500)
                else:
                    st.warning("⚠️ कुनै पनि मतदाता भेटिएन। कृपया फिल्टर परिवर्तन गर्नुहोस्।")
            else:
                st.info("👆 माथिका फिल्टरहरू भर्नुहोस् र 'खोज्नुहोस्' बटन थिच्नुहोस्")
        
        # Statistics in sidebar
        st.sidebar.markdown("---")
        st.sidebar.subheader("तथ्याङ्क")
        st.sidebar.metric("कुल मतदाता", len(df))
        
        if 'लिङ्ग' in df.columns:
            st.sidebar.write("लिङ्ग अनुसार:")
            gender_counts = df['लिङ्ग'].value_counts()
            for gender, count in gender_counts.items():
                st.sidebar.write(f"- {gender}: {count}")
        
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
