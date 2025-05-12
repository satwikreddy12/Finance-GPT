import streamlit as st
from excercise2 import agent_team
from streamlit_lottie import st_lottie
import requests

# Load Lottie animation
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

st.set_page_config(page_title="Financial GPT", page_icon="💰", layout="centered")

# Header with styling
st.markdown("""
    <style>
    .title { font-size: 2.5rem; text-align: center; margin-bottom: 0; }
    .subtitle { font-size: 1.1rem; text-align: center; color: gray; }
    </style>
    <div class='title'>💰 Financial GPT Assistant</div>
    <div class='subtitle'>Smarter answers. Sharper money decisions.</div>
    <hr>
""", unsafe_allow_html=True)

# Add animation
lottie_url = "https://assets9.lottiefiles.com/packages/lf20_n1eynyos.json"
lottie_json = load_lottieurl(lottie_url)
if lottie_json:
    st_lottie(lottie_json, height=180)

# Horizontal radio buttons
mode = st.radio(
    "🧭 Choose Focus Area:",
    ["All", "Budgeting", "Loan Help", "Stock Info", "Financial Advice"],
    horizontal=True
)

# Session storage
if "messages" not in st.session_state:
    st.session_state.messages = []

# Input form
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("💬 Your Question", placeholder="e.g., What is compound interest?")
    submitted = st.form_submit_button("Ask")

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        response = agent_team.run(user_input)
        st.session_state.messages.append({"role": "assistant", "content": response.content})
        st.toast("📤 Answer generated!", icon="🤖")

# Chat display with safe formatting
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"🧑‍💼 **User:** {msg['content']}", unsafe_allow_html=True)
    else:
        st.markdown(f"🤖 **GPT:** {msg['content']}", unsafe_allow_html=True)

# Expandable chat history
with st.expander("🕓 View Full Chat History"):
    for msg in st.session_state.messages:
        role = "You" if msg["role"] == "user" else "GPT"
        st.markdown(f"**{role}**: {msg['content']}")
