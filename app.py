import streamlit as st
import io
import json
import time
import random
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    st.warning("Transformers not available. Using fallback responses.")

try:
    import plotly.express as px
    import pandas as pd
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

PDF_AVAILABLE = False
PDF_LIBRARY = None

try:
    import pdfplumber
    PDF_AVAILABLE = True
    PDF_LIBRARY = "pdfplumber"
except ImportError:
    st.warning("PDF processing not available. Install: pip install pdfplumber")

# Load FAQ data
@st.cache_data
def load_faq_data():
    try:
        with open('college_faq.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("college_faq.json not found. Please ensure the file exists.")
        return []

faq_data = load_faq_data()

# Page config
st.set_page_config(
    page_title="College Admission Chatbot",
    page_icon="🎓",
    layout="wide"
)

# CSS Styling
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.chat-container {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    border: 1px solid #e9ecef;
}

.answer-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.sidebar-section {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #667eea;
}

.notification-detail {
    background: #e7f3ff;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #0dcaf0;
}

@keyframes bounce {
    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-10px); }
    60% { transform: translateY(-5px); }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

# Language selection
language = st.selectbox("🌐 Language / भाषा / மொழி", ["English", "Hindi", "Tamil"], key="language_select")

# Translations
# Translations
translations = {
    "English": {
        "title": "🎓 College Admission Chatbot",
        "subtitle": "Ask any question about admissions, courses, fees, dates, and more!",
        "input_placeholder": "e.g., What is the eligibility for B.Tech?",
        "detected_intent": "🎯 Detected Intent:",
        "answer": "🤖 Answer:",
        "conversation_history": "💬 Conversation History",
        "quick_questions": "🎯 Quick Questions",
        "quick_questions_list": [
            "What is the eligibility for B.Tech?",
            "What are the fees for MBA?",
            "What is the last date to apply?",
            "How much is the hostel fee?",
            "What is the counseling process?"
        ],
        "latest_updates": "📢 Latest Updates",
        "notifications": [
            "🚨 Last Week for Applications",
            "🎓 New Scholarship Program",
            "📅 Exam Dates Announced"
        ],
        "notification_details": [
            "Only 7 days left to submit your application for the August batch!",
            "Merit-based scholarships up to 75% now available. Apply before March 20th!",
            "Entrance exam dates have been announced. Check your email for details."
        ],
        "upload_resume": "📄 Upload Resume",
        "upload_file": "Choose file",
        "get_suggestions": "Get Course Suggestions",
        "recommended_courses": "Recommended Courses:",
        "upload_detailed": "Upload a more detailed resume for better suggestions.",
        "contact_support": "📞 **Need Help?** Contact: admissions@college.edu | +91-1234567890"
    },
    "Hindi": {
        "title": "🎓 कॉलेज प्रवेश चैटबॉट",
        "subtitle": "प्रवेश, कोर्स, फीस, तारीखों के बारे में कोई भी प्रश्न पूछें!",
        "input_placeholder": "जैसे, B.Tech के लिए योग्यता क्या है?",
        "detected_intent": "🎯 पहचाना गया इरादा:",
        "answer": "🤖 उत्तर:",
        "conversation_history": "💬 बातचीत का इतिहास",
        "quick_questions": "🎯 त्वरित प्रश्न",
        "quick_questions_list": [
            "B.Tech के लिए योग्यता क्या है?",
            "MBA की फीस क्या है?",
            "आवेदन की अंतिम तारीख क्या है?",
            "हॉस्टल की फीस कितनी है?",
            "काउंसलिंग प्रक्रिया क्या है?"
        ],
        "latest_updates": "📢 नवीनतम अपडेट",
        "notifications": [
            "🚨 आवेदन के लिए अंतिम सप्ताह",
            "🎓 नया छात्रवृत्ति कार्यक्रम",
            "📅 परीक्षा तिथियां घोषित"
        ],
        "notification_details": [
            "अगस्त बैच के लिए आवेदन जमा करने के लिए केवल 7 दिन बचे हैं!",
            "75% तक मेधा आधारित छात्रवृत्ति उपलब्ध। 20 मार्च से पहले आवेदन करें!",
            "प्रवेश परीक्षा की तारीखें घोषित की गई हैं। विवरण के लिए अपना ईमेल चेक करें।"
        ],
        "upload_resume": "📄 रिज्यूमे अपलोड करें",
        "upload_file": "फाइल चुनें",
        "get_suggestions": "कोर्स सुझाव प्राप्त करें",
        "recommended_courses": "अनुशंसित कोर्स:",
        "upload_detailed": "बेहतर सुझावों के लिए अधिक विस्तृत रिज्यूमे अपलोड करें।",
        "contact_support": "📞 **सहायता चाहिए?** संपर्क: admissions@college.edu | +91-1234567890"
    },
    "Tamil": {
        "title": "🎓 கல்லூரி சேர்க்கை சாட்போட்",
        "subtitle": "சேர்க்கை, படிப்புகள், கட்டணம், தேதிகள் பற்றி எந்த கேள்வியும் கேளுங்கள்!",
        "input_placeholder": "உதாரணம், B.Tech-க்கான தகுதி என்ன?",
        "detected_intent": "🎯 கண்டறியப்பட்ட நோக்கம்:",
        "answer": "🤖 பதில்:",
        "conversation_history": "💬 உரையாடல் வரலாறு",
        "quick_questions": "🎯 விரைவு கேள்விகள்",
        "quick_questions_list": [
            "B.Tech-க்கான தகுதி என்ன?",
            "MBA கட்டணம் என்ன?",
            "விண்ணப்பிக்க கடைசி தேதி என்ன?",
            "விடுதி கட்டணம் எவ்வளவு?",
            "ஆலோசனை செயல்முறை என்ன?"
        ],
        "latest_updates": "📢 சமீபத்திய புதுப்பிப்புகள்",
        "notifications": [
            "🚨 விண்ணப்பங்களுக்கான கடைசி வாரம்",
            "🎓 புதிய உscholarship திட்டம்",
            "📅 தேர்வு தேதிகள் அறிவிக்கப்பட்டன"
        ],
        "notification_details": [
            "ஆகஸ்ட் batch-க்கு விண்ணப்பம் சமர்ப்பிக்க 7 நாட்கள் மட்டுமே உள்ளன!",
            "75% வரை merit அடிப்படையிலான உதவித்தொகை கிடைக்கிறது. மார்ச் 20-க்கு முன் விண்ணப்பிக்கவும்!",
            "நுழைவுத் தேர்வு தேதிகள் அறிவிக்கப்பட்டுள்ளன. விவரங்களுக்கு உங்கள் மின்னஞ்சலைச் சரிபார்க்கவும்."
        ],
        "upload_resume": "📄 Resume பதிவேற்றவும்",
        "upload_file": "கோப்பைத் தேர்ந்தெடுக்கவும்",
        "get_suggestions": "படிப்பு பரிந்துரைகளைப் பெறவும்",
        "recommended_courses": "பரிந்துரைக்கப்பட்ட படிப்புகள்:",
        "upload_detailed": "சிறந்த பரிந்துரைகளுக்கு மிகவும் விரிவான resume பதிவேற்றவும்।",
        "contact_support": "📞 **உதவி தேவையா?** தொடர்பு: admissions@college.edu | +91-1234567890"
    }
}
t = translations[language]

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'selected_notification' not in st.session_state:
    st.session_state.selected_notification = None
if 'analytics' not in st.session_state:
    st.session_state.analytics = {
        'questions_asked': 0,
        'languages_used': {},
        'intents_detected': {},
        'user_ratings': [],
        'session_start': datetime.now(),
        'response_times': [],
        'satisfaction_scores': []
    }
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        'show_confidence': True,
        'typing_animation': True,
        'auto_suggestions': True
    }
if 'show_analytics' not in st.session_state:
    st.session_state.show_analytics = False

# Header
st.markdown(f'<div class="main-header"><h1>{t["title"]}</h1><p style="margin-top: 1rem; font-size: 1.1rem; opacity: 0.9;">{t["subtitle"]}</p></div>', unsafe_allow_html=True)

# Load model
@st.cache_resource
def load_model():
    if TRANSFORMERS_AVAILABLE:
        try:
            return pipeline("text2text-generation", model="google/flan-t5-small", local_files_only=True)
        except Exception as e:
            st.warning(f"Offline model not available. Using rule-based responses. Error: {e}")
            return None
    return None

qa_pipeline = load_model() if TRANSFORMERS_AVAILABLE else None

if not TRANSFORMERS_AVAILABLE or qa_pipeline is None:
    st.info("🔄 Running in offline mode with rule-based responses. All basic features are available!")
else:
    st.success("🤖 AI model loaded successfully!")

# PDF processing function
def extract_text_from_pdf(pdf_file):
    if not PDF_AVAILABLE:
        st.error("PDF processing not available. Please upload a TXT file instead.")
        return ""
    
    try:
        if PDF_LIBRARY == "pdfplumber":
            with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""

# Enhanced answer function with confidence scoring
def get_answer_with_confidence(question):
    start_time = time.time()
    question_lower = question.lower().strip()
    confidence = 0.0
    
    # First, try exact match from JSON data
    for item in faq_data:
        if question_lower == item['prompt'].lower().strip():
            response_time = time.time() - start_time
            return item['response'], 1.0, response_time
    
    # Enhanced keyword matching for better responses
    best_match = None
    max_score = 0
    
    for item in faq_data:
        prompt_lower = item['prompt'].lower()
        score = 0
        
        # Count matching words
        question_words = set(question_lower.split())
        prompt_words = set(prompt_lower.split())
        common_words = question_words.intersection(prompt_words)
        
        if common_words:
            score = len(common_words) / len(question_words.union(prompt_words))
            
        # Boost score for key terms
        if 'scholarship' in question_lower and 'scholarship' in prompt_lower:
            score += 0.5
        if 'fee' in question_lower and 'fee' in prompt_lower:
            score += 0.3
            
        if score > max_score and score > 0.2:
            max_score = score
            best_match = item['response']
            confidence = score
    
    if best_match:
        response_time = time.time() - start_time
        return best_match, confidence, response_time
    
    # Specific fallback for scholarship questions
    if 'scholarship' in question_lower:
        response_time = time.time() - start_time
        return "Scholarships are available for meritorious and economically weaker students. Please check the scholarship section on our website for detailed information and application procedures.", 0.7, response_time
    
    # General fallback response
    response_time = time.time() - start_time
    fallback_answer = "I'm sorry, I don't have specific information about that. Please contact our admissions office at admissions@college.edu or call +91-1234567890 for detailed assistance."
    return fallback_answer, 0.3, response_time

# Keep original get_answer for backward compatibility
def get_answer(question):
    answer, confidence, response_time = get_answer_with_confidence(question)
    return answer

def classify_intent(question):
    question_lower = question.lower()
    
    # Check if question exists in FAQ data
    for item in faq_data:
        if question_lower in item['prompt'].lower() or item['prompt'].lower() in question_lower:
            # Classify based on content
            prompt_lower = item['prompt'].lower()
            if any(word in prompt_lower for word in ['fee', 'cost', 'payment', 'money']):
                return 'fees'
            elif any(word in prompt_lower for word in ['date', 'deadline', 'when', 'time']):
                return 'dates'
            elif any(word in prompt_lower for word in ['eligibility', 'criteria', 'requirement']):
                return 'eligibility'
            elif any(word in prompt_lower for word in ['course', 'program', 'degree']):
                return 'courses'
            elif any(word in prompt_lower for word in ['admission', 'apply', 'process']):
                return 'admission'
    
    # Fallback to original classification
    intents = {
        'fees': ['fee', 'cost', 'payment', 'money', 'scholarship'],
        'dates': ['date', 'deadline', 'when', 'time', 'exam', 'result'],
        'eligibility': ['eligibility', 'criteria', 'requirement', 'qualify'],
        'courses': ['course', 'program', 'degree', 'branch', 'subject'],
        'admission': ['admission', 'apply', 'process', 'form'],
        'hostel': ['hostel', 'accommodation', 'room'],
        'placement': ['placement', 'job', 'career', 'company']
    }
    
    for intent, keywords in intents.items():
        if any(word in question_lower for word in keywords):
            return intent
    return 'general'

# Enhanced chat interface
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Interactive input row
col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
with col1:
    user_input = st.text_input("💬", placeholder=t["input_placeholder"], label_visibility="collapsed", key="main_input")
with col2:
    if st.button("🎤", help="Voice Input (Coming Soon)", key="voice_btn"):
        st.info("🎤 Voice input feature coming soon!")
with col3:
    if st.button("🔍", help="Search Chat", key="search_btn"):
        st.session_state.show_search = not st.session_state.get('show_search', False)
with col4:
    if st.button("📊", help="Analytics", key="analytics_btn"):
        st.session_state.show_analytics = not st.session_state.get('show_analytics', False)

# Search functionality
if st.session_state.get('show_search', False):
    search_term = st.text_input("🔍 Search conversations:", key="search_input")
    if search_term and st.session_state.conversation_history:
        st.write("**Search Results:**")
        for i, qa in enumerate(st.session_state.conversation_history):
            if search_term.lower() in qa['question'].lower() or search_term.lower() in qa['answer'].lower():
                st.write(f"**Q:** {qa['question']}")
                st.write(f"**A:** {qa['answer'][:100]}...")
                st.write("---")

# Analytics dashboard
if st.session_state.get('show_analytics', False):
    st.markdown("### 📊 Session Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Questions Asked", st.session_state.analytics['questions_asked'])
    with col2:
        avg_rating = sum(st.session_state.analytics['user_ratings']) / len(st.session_state.analytics['user_ratings']) if st.session_state.analytics['user_ratings'] else 0
        st.metric("Avg Rating", f"{avg_rating:.1f}⭐")
    with col3:
        session_duration = (datetime.now() - st.session_state.analytics['session_start']).seconds // 60
        st.metric("Session Duration", f"{session_duration} min")
    with col4:
        avg_response_time = sum(st.session_state.analytics['response_times']) / len(st.session_state.analytics['response_times']) if st.session_state.analytics['response_times'] else 0
        st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
    
    # Intent distribution chart
    if PLOTLY_AVAILABLE and st.session_state.analytics['intents_detected']:
        try:
            intent_df = pd.DataFrame(list(st.session_state.analytics['intents_detected'].items()), 
                                    columns=['Intent', 'Count'])
            fig = px.pie(intent_df, values='Count', names='Intent', title='Question Categories')
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")
    
    # Language usage chart
    if PLOTLY_AVAILABLE and st.session_state.analytics['languages_used']:
        try:
            lang_df = pd.DataFrame(list(st.session_state.analytics['languages_used'].items()), 
                                  columns=['Language', 'Count'])
            fig_lang = px.bar(lang_df, x='Language', y='Count', title='Language Usage')
            st.plotly_chart(fig_lang, use_container_width=True)
        except Exception as e:
            st.error(f"Language chart error: {e}")
    
    # Response time trend
    if st.session_state.analytics['response_times']:
        try:
            response_times = st.session_state.analytics['response_times'][-20:]  # Last 20 responses
            fig_time = px.line(x=range(len(response_times)), y=response_times, 
                              title='Response Time Trend', 
                              labels={'x': 'Question Number', 'y': 'Response Time (s)'})
            st.plotly_chart(fig_time, use_container_width=True)
        except Exception as e:
            st.error(f"Response time chart error: {e}")
    
    # Hide analytics button
    if st.button("❌ Hide Analytics", key="hide_analytics"):
        st.session_state.show_analytics = False
        st.rerun()

# Main chat processing
if user_input:
    # Show typing indicator
    with st.spinner("🤔 Thinking..."):
        time.sleep(0.5)  # Simulate processing time
        
    intent = classify_intent(user_input)
    answer, confidence, response_time = get_answer_with_confidence(user_input)
    
    # Display intent
    st.info(f"🎯 {t['detected_intent']} **{intent.title()}**")
    
    # Display answer with Streamlit components
    st.markdown("### 🤖 Answer:")
    
    # Answer in a nice container
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
        ">
            <div style="font-size: 1.1rem; line-height: 1.6;">
                {answer}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Metrics in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        confidence_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.5 else "🔴"
        st.metric("Confidence", f"{confidence:.0%}", delta=confidence_emoji)
    with col2:
        st.metric("Response Time", f"{response_time:.2f}s")
    with col3:
        st.metric("Category", intent.title())
    
    # Rating system - Enhanced UI with gradients and colors
    st.markdown("**⭐ Rate this response:**")
    
    # Add custom CSS for rating buttons
    st.markdown("""
    <style>
    .rating-button {
        background: linear-gradient(45deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
        border: none;
        border-radius: 15px;
        padding: 0.5rem 1rem;
        color: white;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        box-shadow: 0 4px 15px rgba(255, 154, 158, 0.4);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .rating-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 154, 158, 0.6);
        background: linear-gradient(45deg, #ff6b6b 0%, #ff8e8e 50%, #ffb3b3 100%);
    }
    
    .rating-button-1 {
        background: linear-gradient(45deg, #ff6b6b 0%, #ee5a52 100%);
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
    }
    
    .rating-button-2 {
        background: linear-gradient(45deg, #ffa726 0%, #ff9800 100%);
        box-shadow: 0 4px 15px rgba(255, 167, 38, 0.4);
    }
    
    .rating-button-3 {
        background: linear-gradient(45deg, #ffeb3b 0%, #ffc107 100%);
        box-shadow: 0 4px 15px rgba(255, 235, 59, 0.4);
    }
    
    .rating-button-4 {
        background: linear-gradient(45deg, #8bc34a 0%, #4caf50 100%);
        box-shadow: 0 4px 15px rgba(139, 195, 74, 0.4);
    }
    
    .rating-button-5 {
        background: linear-gradient(45deg, #4caf50 0%, #2e7d32 100%);
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .rating-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .rating-title {
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create rating container with gradient background
    st.markdown('<div class="rating-container">', unsafe_allow_html=True)
    st.markdown('<div class="rating-title">⭐ Rate this response:</div>', unsafe_allow_html=True)
    
    # Create unique key for this response
    current_question = user_input
    rating_key = f"rating_{hash(current_question)}_{len(st.session_state.conversation_history)}"
    
    # Initialize rating in session state if not exists
    if rating_key not in st.session_state:
        st.session_state[rating_key] = 0
    
    # Create 5 rating buttons in columns with custom styling
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⭐", key=f"btn1_{rating_key}", use_container_width=True, type="secondary"):
            st.session_state[rating_key] = 1
    
    with col2:
        if st.button("⭐⭐", key=f"btn2_{rating_key}", use_container_width=True, type="secondary"):
            st.session_state[rating_key] = 2
    
    with col3:
        if st.button("⭐⭐⭐", key=f"btn3_{rating_key}", use_container_width=True, type="secondary"):
            st.session_state[rating_key] = 3
    
    with col4:
        if st.button("⭐⭐⭐⭐", key=f"btn4_{rating_key}", use_container_width=True, type="secondary"):
            st.session_state[rating_key] = 4
    
    with col5:
        if st.button("⭐⭐⭐⭐⭐", key=f"btn5_{rating_key}", use_container_width=True, type="primary"):
            st.session_state[rating_key] = 5
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get current rating from session state
    current_rating = st.session_state[rating_key]
    
    # Show feedback if rating was given
    if current_rating > 0:
        st.balloons()
        st.success(f"🎉 You rated: {current_rating} star{'s' if current_rating > 1 else ''}!")
        
        # Enhanced feedback with animated gradient
        descriptions = {1: "Poor", 2: "Fair", 3: "Good", 4: "Very Good", 5: "Excellent"}
        colors = {
            1: "linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%)",
            2: "linear-gradient(135deg, #ffa726 0%, #ff9800 100%)", 
            3: "linear-gradient(135deg, #ffeb3b 0%, #ffc107 100%)",
            4: "linear-gradient(135deg, #8bc34a 0%, #4caf50 100%)",
            5: "linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)"
        }
        
        # Add bounce animation CSS first
        st.markdown("""
        <style>
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: scale(1.02) translateY(0); }
            40% { transform: scale(1.02) translateY(-10px); }
            60% { transform: scale(1.02) translateY(-5px); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Then add the feedback box
        feedback_html = f"""
        <div style="
            background: {colors[current_rating]};
            color: white;
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
            transform: scale(1.02);
            animation: bounce 0.6s ease-in-out;
        ">
            <h2 style="margin: 0; font-size: 1.5rem;">🎉 Thank you for your feedback!</h2>
            <div style="font-size: 3rem; margin: 1rem 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                {'⭐' * current_rating}
            </div>
            <h3 style="margin: 0; font-size: 1.3rem;">
                You rated: <strong>{descriptions[current_rating]}</strong>
            </h3>
            <p style="font-size: 1rem; opacity: 0.9; margin-top: 0.5rem;">
                Your feedback helps us improve! 🚀
            </p>
        </div>
        """
        
        st.markdown(feedback_html, unsafe_allow_html=True)
        
        # Contextual message with matching colors
        if current_rating >= 4:
            st.success("🎯 Awesome! We're thrilled you found our response helpful!")
        elif current_rating == 3:
            st.info("👍 Thank you! We're always working to improve.")
        else:
            st.warning("📝 Thanks for the feedback! We'll work harder to help you better.")
        
        # Add to analytics only once
        if current_rating not in st.session_state.analytics['user_ratings']:
            st.session_state.analytics['user_ratings'].append(current_rating)
    
    # Update analytics
    st.session_state.analytics['questions_asked'] += 1
    st.session_state.analytics['languages_used'][language] = st.session_state.analytics['languages_used'].get(language, 0) + 1
    st.session_state.analytics['intents_detected'][intent] = st.session_state.analytics['intents_detected'].get(intent, 0) + 1
    st.session_state.analytics['response_times'].append(response_time)
    
    # Save conversation with current rating (will be 0 initially, updated when user rates)
    conversation_entry = {
        'question': user_input,
        'answer': answer,
        'intent': intent,
        'confidence': confidence,
        'response_time': response_time,
        'rating': current_rating,
        'timestamp': datetime.now().isoformat()
    }
    
    # Check if this conversation already exists, if so update it
    existing_index = None
    for i, conv in enumerate(st.session_state.conversation_history):
        if conv['question'] == user_input and conv['answer'] == answer:
            existing_index = i
            break
    
    if existing_index is not None:
        st.session_state.conversation_history[existing_index] = conversation_entry
    else:
        st.session_state.conversation_history.append(conversation_entry)

st.markdown('</div>', unsafe_allow_html=True)

    
# Conversation History
if st.session_state.conversation_history:
    st.markdown(f'<div class="sidebar-section"><h3>{t["conversation_history"]}</h3></div>', unsafe_allow_html=True)
    
    # Search and filter options
    col1, col2 = st.columns(2)
    with col1:
        history_search = st.text_input("🔍 Search history:", key="history_search")
    with col2:
        intent_options = ["All"] + list(set([qa.get('intent', 'Unknown') for qa in st.session_state.conversation_history]))
        intent_filter = st.selectbox("Filter by category:", intent_options, key="intent_filter")
    
    # Filter conversations
    filtered_history = st.session_state.conversation_history
    if history_search:
        filtered_history = [qa for qa in filtered_history 
                          if history_search.lower() in qa['question'].lower() or history_search.lower() in qa['answer'].lower()]
    if intent_filter != "All":
        filtered_history = [qa for qa in filtered_history if qa.get('intent') == intent_filter]
    
    # Display conversations
    for i, qa in enumerate(reversed(filtered_history[-5:]), 1):
        confidence = qa.get('confidence', 0)
        confidence_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.5 else "🔴"
        rating_display = "⭐" * qa.get('rating', 0) if qa.get('rating') else "⚪ No rating"
        
        with st.expander(f"{confidence_emoji} Q{len(filtered_history)-i+1}: {qa['question'][:50]}... | {rating_display}"):
            st.markdown(f"**👤 Question:** {qa['question']}")
            st.markdown(f"**🤖 Answer:** {qa['answer']}")
            
            # Metadata
            meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
            with meta_col1:
                st.write(f"**📂 Category:** {qa.get('intent', 'Unknown').title()}")
            with meta_col2:
                st.write(f"**🎯 Confidence:** {confidence:.0%}")
            with meta_col3:
                st.write(f"**⏱️ Response:** {qa.get('response_time', 0):.2f}s")
            with meta_col4:
                timestamp = qa.get('timestamp', '')
                if timestamp:
                    time_str = timestamp[:16].replace('T', ' ')
                    st.write(f"**🕐 Time:** {time_str}")

# Sidebar features
st.sidebar.markdown(f'<div class="sidebar-section"><h3>{t["quick_questions"]}</h3></div>', unsafe_allow_html=True)

for q in t["quick_questions_list"]:
    if st.sidebar.button(q, key=f"quick_{hash(q)}"):
        st.session_state.temp_question = q

# Handle quick question clicks
if hasattr(st.session_state, 'temp_question'):
    intent = classify_intent(st.session_state.temp_question)
    answer, confidence, response_time = get_answer_with_confidence(st.session_state.temp_question)
    
    # Display intent
    st.info(f"🎯 {t['detected_intent']} **{intent.title()}**")
    
    # Display answer
    st.markdown("### 🤖 Answer:")
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
        ">
            <div style="font-size: 1.1rem; line-height: 1.6;">
                {answer}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Metrics for quick question
    col1, col2, col3 = st.columns(3)
    with col1:
        confidence_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.5 else "🔴"
        st.metric("Confidence", f"{confidence:.0%}", delta=confidence_emoji)
    with col2:
        st.metric("Response Time", f"{response_time:.2f}s")
    with col3:
        st.metric("Category", intent.title())
    
    # Rating for quick question - Enhanced UI with gradients
    st.markdown("**⭐ Rate this response:**")
    
    # Create rating container with gradient background
    st.markdown('<div class="rating-container">', unsafe_allow_html=True)
    st.markdown('<div class="rating-title">⭐ Rate this response:</div>', unsafe_allow_html=True)
    
    # Create unique key
    quick_id = f"quick_{len(st.session_state.conversation_history)}"
    quick_rating_key = f"rating_{quick_id}"
    
    # Initialize rating in session state
    if quick_rating_key not in st.session_state:
        st.session_state[quick_rating_key] = 0
    
    # Create 5 rating buttons with enhanced styling
    qcol1, qcol2, qcol3, qcol4, qcol5 = st.columns(5)
    
    with qcol1:
        if st.button("⭐", key=f"qbtn1_{quick_id}", use_container_width=True, type="secondary"):
            st.session_state[quick_rating_key] = 1
    
    with qcol2:
        if st.button("⭐⭐", key=f"qbtn2_{quick_id}", use_container_width=True, type="secondary"):
            st.session_state[quick_rating_key] = 2
    
    with qcol3:
        if st.button("⭐⭐⭐", key=f"qbtn3_{quick_id}", use_container_width=True, type="secondary"):
            st.session_state[quick_rating_key] = 3
    
    with qcol4:
        if st.button("⭐⭐⭐⭐", key=f"qbtn4_{quick_id}", use_container_width=True, type="secondary"):
            st.session_state[quick_rating_key] = 4
    
    with qcol5:
        if st.button("⭐⭐⭐⭐⭐", key=f"qbtn5_{quick_id}", use_container_width=True, type="primary"):
            st.session_state[quick_rating_key] = 5
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get current rating
    rating = st.session_state[quick_rating_key]
    
    # Show feedback if rating was given
    if rating > 0:
        st.balloons()
        st.success(f"🎉 You rated: {rating} star{'s' if rating > 1 else ''}!")
        
        # Add to analytics
        st.session_state.analytics['user_ratings'].append(rating)
        
        # Enhanced feedback with matching colors
        descriptions = {1: "Poor", 2: "Fair", 3: "Good", 4: "Very Good", 5: "Excellent"}
        colors = {
            1: "linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%)",
            2: "linear-gradient(135deg, #ffa726 0%, #ff9800 100%)", 
            3: "linear-gradient(135deg, #ffeb3b 0%, #ffc107 100%)",
            4: "linear-gradient(135deg, #8bc34a 0%, #4caf50 100%)",
            5: "linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)"
        }
        
        # Add bounce animation CSS first
        st.markdown("""
        <style>
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: scale(1.02) translateY(0); }
            40% { transform: scale(1.02) translateY(-10px); }
            60% { transform: scale(1.02) translateY(-5px); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Then add the feedback box
        feedback_html = f"""
        <div style="
            background: {colors[rating]};
            color: white;
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
            transform: scale(1.02);
            animation: bounce 0.6s ease-in-out;
        ">
            <h2 style="margin: 0; font-size: 1.5rem;">🎉 Thank you for your feedback!</h2>
            <div style="font-size: 3rem; margin: 1rem 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                {'⭐' * rating}
            </div>
            <h3 style="margin: 0; font-size: 1.3rem;">
                You rated: <strong>{descriptions[rating]}</strong>
            </h3>
            <p style="font-size: 1rem; opacity: 0.9; margin-top: 0.5rem;">
                Your feedback helps us improve! 🚀
            </p>
        </div>
        """
        
        st.markdown(feedback_html, unsafe_allow_html=True)
        
        # Contextual message
        if rating >= 4:
            st.success("🎯 Awesome! We're thrilled you found our response helpful!")
        elif rating == 3:
            st.info("👍 Thank you! We're always working to improve.")
        else:
            st.warning("📝 Thanks for the feedback! We'll work harder to help you better.")
    
    # Save to conversation history with current rating
    st.session_state.conversation_history.append({
        'question': st.session_state.temp_question,
        'answer': answer,
        'intent': intent,
        'confidence': confidence,
        'response_time': response_time,
        'rating': rating,
        'timestamp': datetime.now().isoformat()
    })
    
    del st.session_state.temp_question
    st.rerun()

# Notifications
st.sidebar.markdown("---")
st.sidebar.markdown(f'<div class="sidebar-section"><h3>{t["latest_updates"]}</h3></div>', unsafe_allow_html=True)

for i, notification in enumerate(t["notifications"]):
    if st.sidebar.button(notification, key=f"notif_{i}"):
        st.session_state.selected_notification = i

# Display notification details
if st.session_state.selected_notification is not None:
    detail = t["notification_details"][st.session_state.selected_notification]
    st.markdown(f'<div class="notification-detail">{detail}</div>', unsafe_allow_html=True)

# Resume upload
st.sidebar.markdown("---")
st.sidebar.markdown(f'<div class="sidebar-section"><h3>{t["upload_resume"]}</h3></div>', unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader(t["upload_file"], type=['pdf', 'txt'], key="resume_upload")

if uploaded_file:
    resume_text = ""
    if uploaded_file.type == "text/plain":
        resume_text = str(uploaded_file.read(), "utf-8")
    elif uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    
    if resume_text and st.sidebar.button(t["get_suggestions"], key="get_suggestions"):
        suggestions = []
        resume_lower = resume_text.lower()
        
        if any(word in resume_lower for word in ['programming', 'coding', 'software', 'python', 'java']):
            suggestions.append("B.Tech Computer Science Engineering")
        if any(word in resume_lower for word in ['electronics', 'circuits', 'embedded']):
            suggestions.append("B.Tech Electronics & Communication")
        if any(word in resume_lower for word in ['management', 'business', 'marketing', 'finance']):
            suggestions.append("MBA")
        if any(word in resume_lower for word in ['mechanical', 'automobile', 'manufacturing']):
            suggestions.append("B.Tech Mechanical Engineering")
        
        if suggestions:
            st.sidebar.success(t["recommended_courses"])
            for course in suggestions:
                st.sidebar.write(f"• {course}")
        else:
            st.sidebar.info(t["upload_detailed"])

# Settings panel
st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ Settings", expanded=False):
    st.session_state.user_preferences['show_confidence'] = st.checkbox("Show Confidence Scores", 
                                                                      value=st.session_state.user_preferences.get('show_confidence', True))
    st.session_state.user_preferences['typing_animation'] = st.checkbox("Typing Animation", 
                                                                       value=st.session_state.user_preferences.get('typing_animation', True))
    st.session_state.user_preferences['auto_suggestions'] = st.checkbox("Auto Suggestions", 
                                                                        value=st.session_state.user_preferences.get('auto_suggestions', True))
    
    if st.button("🔄 Reset All Settings", key="reset_settings"):
        st.session_state.user_preferences = {
            'show_confidence': True,
            'typing_animation': True,
            'auto_suggestions': True
        }
        st.success("Settings reset!")

# Quick stats
st.sidebar.markdown("## 📈 Quick Stats")
stats_col1, stats_col2 = st.sidebar.columns(2)
with stats_col1:
    st.metric("Questions", st.session_state.analytics['questions_asked'])
    avg_rating = sum(st.session_state.analytics['user_ratings']) / len(st.session_state.analytics['user_ratings']) if st.session_state.analytics['user_ratings'] else 0
    st.metric("Avg Rating", f"{avg_rating:.1f}⭐")
with stats_col2:
    session_duration = (datetime.now() - st.session_state.analytics['session_start']).seconds // 60
    st.metric("Session", f"{session_duration}m")
    if st.session_state.analytics['response_times']:
        avg_response = sum(st.session_state.analytics['response_times']) / len(st.session_state.analytics['response_times'])
        st.metric("Avg Speed", f"{avg_response:.1f}s")

# Quick actions
st.sidebar.markdown("## ⚡ Quick Actions")
if st.sidebar.button("🎲 Random Question", key="random_question_action"):
    if faq_data:
        random_qa = random.choice(faq_data)
        st.session_state.temp_question = random_qa['prompt']

if st.sidebar.button("📊 Show Full Analytics", key="show_analytics_action"):
    st.session_state.show_analytics = True

if st.sidebar.button("🧹 Clear All Data", key="clear_data_action"):
    if st.sidebar.button("⚠️ Confirm Clear All", type="secondary", key="confirm_clear_action"):
        st.session_state.conversation_history = []
        st.session_state.analytics = {
            'questions_asked': 0,
            'languages_used': {},
            'intents_detected': {},
            'user_ratings': [],
            'session_start': datetime.now(),
            'response_times': [],
            'satisfaction_scores': []
        }
        st.success("All data cleared!")
        st.rerun()

# Export functionality
if st.session_state.conversation_history:
    st.sidebar.markdown("## 📥 Export Options")
    
    export_format = st.sidebar.selectbox("Format:", ["JSON", "CSV", "TXT"], key="export_format_select")
    
    if st.sidebar.button("📥 Export Chat", key="export_chat_action"):
        if export_format == "JSON":
            data = json.dumps(st.session_state.conversation_history, indent=2, ensure_ascii=False)
            st.sidebar.download_button(
                "Download JSON", 
                data, 
                f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                "application/json",
                key="download_json_btn"
            )
        elif export_format == "CSV":
            if PLOTLY_AVAILABLE:
                df = pd.DataFrame(st.session_state.conversation_history)
                csv_data = df.to_csv(index=False)
                st.sidebar.download_button(
                    "Download CSV", 
                    csv_data, 
                    f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                    "text/csv",
                    key="download_csv_btn"
                )
            else:
                st.sidebar.error("Pandas not available for CSV export")
        else:  # TXT
            txt_data = f"College Admission Chat History\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}\n\n"
            for i, qa in enumerate(st.session_state.conversation_history, 1):
                txt_data += f"Q{i}: {qa['question']}\n"
                txt_data += f"A{i}: {qa['answer']}\n"
                txt_data += f"Category: {qa.get('intent', 'Unknown')}\n"
                txt_data += f"Confidence: {qa.get('confidence', 0):.0%}\n"
                txt_data += f"Rating: {'⭐' * qa.get('rating', 0) if qa.get('rating') else 'No rating'}\n"
                txt_data += f"Time: {qa.get('timestamp', 'Unknown')}\n"
                txt_data += "="*50 + "\n\n"
            
            st.sidebar.download_button(
                "Download TXT", 
                txt_data, 
                f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
                "text/plain",
                key="download_txt_btn"
            )

# Debug section
if st.sidebar.checkbox("🔍 Debug Mode", key="debug_mode_check"):
    st.sidebar.markdown("### Available Questions:")
    for i, item in enumerate(faq_data[:10]):  # Show first 10
        st.sidebar.text(f"{i+1}. {item['prompt'][:50]}...")
    
    if len(faq_data) > 10:
        st.sidebar.text(f"... and {len(faq_data) - 10} more questions")
    
    st.sidebar.markdown(f"**Total FAQ items:** {len(faq_data)}")

# Contact info
st.markdown("---")
st.markdown(t["contact_support"])
