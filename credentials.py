import os
import streamlit as st

# 1. Try loading .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_credential(key):
    # Check Environment Variable first (Local)
    value = os.getenv(key)
    if value:
        return value.strip()
    
    # Check Streamlit Secrets second (Cloud)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except (FileNotFoundError, AttributeError):
        pass
        
    return ""

USERNAME = get_credential("VOTER_APP_USERNAME")
PASSWORD = get_credential("VOTER_APP_PASSWORD")