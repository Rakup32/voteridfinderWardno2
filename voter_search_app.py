import pandas as pd
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="मतदाता सूची खोज प्रणाली",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("🗳️ मतदाता सूची खोज प्रणाली")
st.markdown("**Voter List Search System**")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('voterlist.xlsx')
    return df

try:
    df = load_data()
    
    # Sidebar for search options
    st.sidebar.header("खोज विकल्प")
    
    search_option = st.sidebar.selectbox(
        "खोज प्रकार छान्नुहोस्:",
        ["सबै डाटा हेर्नुहोस्", "मतदाताको नामबाट खोज्नुहोस्", "मतदाता नंबरबाट खोज्नुहोस्", 
         "लिङ्गबाट फिल्टर गर्नुहोस्", "उमेर दायराबाट खोज्नुहोस्"]
    )
    
    # Display based on search option
    if search_option == "सबै डाटा हेर्नुहोस्":
        st.subheader("सम्पूर्ण मतदाता सूची")
        st.dataframe(df, use_container_width=True, height=600)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"कुल मतदाता संख्या: {len(df)}")
        with col2:
            # Download button
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 CSV डाउनलोड गर्नुहोस्",
                data=csv,
                file_name="voter_list.csv",
                mime="text/csv"
            )
    
    elif search_option == "मतदाताको नामबाट खोज्नुहोस्":
        st.subheader("मतदाताको नामबाट खोज्नुहोस्")
        search_name = st.text_input("मतदाताको नाम लेख्नुहोस्:", "", key="name_search")
        
        if search_name:
            filtered_df = df[df['मतदाताको नाम'].str.contains(search_name, case=False, na=False)]
            
            if not filtered_df.empty:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.success(f"{len(filtered_df)} मतदाता भेटियो")
                with col2:
                    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 डाउनलोड",
                        data=csv,
                        file_name=f"search_results_{search_name}.csv",
                        mime="text/csv"
                    )
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
