import os
import streamlit as st

# 1. Try loading .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skipping

def get_credential(key):
    """
    Retrieves a credential with the following priority:
    1. System Environment Variable / .env file (Local/Docker)
    2. Streamlit Secrets (Streamlit Cloud)
    3. Returns empty string if not found
    """
    # Check Environment Variable first
    value = os.getenv(key)
    if value:
        return value.strip()
    
    # Check Streamlit Secrets second
    # We use a try-except block because accessing st.secrets locally 
    # without a secrets.toml file might raise a FileNotFoundError.
    try:
        if key in st.secrets:
            return st.secrets[key]
    except (FileNotFoundError, AttributeError):
        pass
        
    return ""

# Fetch the credentials
USERNAME = get_credential("VOTER_APP_USERNAME")
PASSWORD = get_credential("VOTER_APP_PASSWORD")