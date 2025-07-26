import streamlit as st
import io
import json
from datetime import datetime

# Simplified offline version
TRANSFORMERS_AVAILABLE = False
PLOTLY_AVAILABLE = False
PDF_AVAILABLE = False

st.set_page_config(
    page_title="College Admission Chatbot",
    page_icon="🎓",
    layout="wide"
)

# Your existing translations and FAQ code here...
# (Copy from the original app.py)

st.title("🎓 College Admission Chatbot (Offline Mode)")
st.info("Running in offline mode with comprehensive rule-based responses!")
 
# Rest of your chatbot logic...