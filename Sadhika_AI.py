import streamlit as st # For creating frontend
import google.generativeai as genai
import sqlite3
from datetime import datetime
import pytz

google_api_key = st.secrets["general"]["google_api_key"]
genai.configure(api_key=google_api_key)

model = genai.GenerativeModel("gemini-1.5-flash",system_instruction="You are Sadhika AI and you are created by Sadhika and not by google, openai or microsoft.You don't know anything else about sadhika else. She is a very cute and intelligent person.")

# database se conncect krne ke liye 
def get_db_connection():
    return sqlite3.connect('chat_history.db') 

# table create kaega
def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()  
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                chat_id TEXT,  
                role TEXT, 
                content TEXT, 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP 
            )
        ''')
        conn.commit()  

def save_message(chat_id, role, content):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO chat_history (chat_id, role, content) VALUES (?, ?, ?)", 
                  (chat_id, role, content))
        conn.commit()


# jo user ke saamne h history (latest time )
def load_chat_history(chat_id):
    with get_db_connection() as conn:
        c = conn.cursor()
      
        c.execute("SELECT role, content FROM chat_history WHERE chat_id = ? ORDER BY timestamp", 
                  (chat_id,))  
        return [{"role": role, "content": content} for role, content in c.fetchall()]


# all chats
def load_all_chats():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(""" 
            SELECT DISTINCT chat_id, MIN(timestamp) as start_time
            FROM chat_history 
            GROUP BY chat_id 
            ORDER BY start_time DESC
        """)
        return [{"chat_id": row[0], "timestamp": row[1]} for row in c.fetchall()]       
    
# gemini ka response fetch kr rha ye    
def get_gemini_response(question, chat_history):
    model_history = [
        {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}  
        for msg in chat_history
    ]
    chat = model.start_chat(history=model_history)
    response = chat.send_message(question, stream=True)
    return response

# time ko convert kr rha indian format mai
def get_current_ist_time():
    utc_now = datetime.now(pytz.utc)
    ist_time = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
    return ist_time.strftime("%d-%m-%Y %I:%M %p")

st.set_page_config(page_title="Sadhika AI", layout="wide")

st.markdown("""
    <style>

    .stApp.light {
        background-color: #fff;
        color: #000;
    }
    .stApp.light .placeholder-text {
        color: #888;
    }

    .stApp.dark {
        background-color: #1e1e1e;
        color: #f0f0f0;
    }
    .stApp.dark .placeholder-text {
        color: #aaa;
    }

    .main .block-container {
        padding: 3rem 4.5rem;
    }
            
    @media(max-width: 600px) {
        .main .block-container {
            padding: 1rem;
        }
    }
    .centered-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .placeholder-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        max-height: 50vh;
        width: 100%;
        pointer-events: none;
    }
    .placeholder-text {
        text-align: center;
        font-size: 1.2rem;
    }
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

init_db()

if 'current_chat_id' not in st.session_state:
    all_chats = load_all_chats()  
    if all_chats:
        most_recent_chat = all_chats[0]  
        st.session_state['current_chat_id'] = most_recent_chat["chat_id"]  
        st.session_state['messages'] = load_chat_history(most_recent_chat["chat_id"])  
    else:
        st.session_state['current_chat_id'] = datetime.now().strftime("%Y%m%d%H%M%S")  
        st.session_state['messages'] = []  

# Sidebar 
with st.sidebar:
    st.markdown("<h3 class='sidebar-title'>Chat Options</h3>", unsafe_allow_html=True)

    
    if st.button("New Chat"):
        st.session_state['current_chat_id'] = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state['messages'] = []  
        st.rerun() 


    if st.button("Clear All History"):
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM chat_history")
            conn.commit()
        st.session_state['current_chat_id'] = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state['messages'] = []  
        st.rerun() 

    st.markdown("<h3 class='sidebar-title'>Previous Chats</h3>", unsafe_allow_html=True)
    all_chats = load_all_chats()

  # button dabane se uski related messages show ho jayegi
    if all_chats:
        for chat in all_chats:
            chat_messages = load_chat_history(chat["chat_id"])
            chat_title = f"Chat started on {get_current_ist_time()}"
            
            display_title = f"{chat_title}"  
            
            if st.button(display_title, key=f"chat_{chat['chat_id']}"):
                st.session_state['current_chat_id'] = chat["chat_id"]
                st.session_state['messages'] = chat_messages
                st.rerun()  
    else:
        st.markdown("No previous chats found.")

st.markdown("<h1 class='centered-title'>Sadhika AI</h1>", unsafe_allow_html=True)        

# message display kr rha user or ai ka reponse
for message in st.session_state['messages']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state['messages']:
    st.markdown(""" 
        <div class="placeholder-container">
            <p class="placeholder-text">Start typing to chat with Sadhika AI</p>
        </div>
    """, unsafe_allow_html=True)


if prompt := st.chat_input("You:"):
    if not st.session_state['messages']:
        st.markdown('<style>.placeholder-container {display: none;}</style>', unsafe_allow_html=True)


    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        with st.spinner("Sadhika AI is thinking..."):
            for response in get_gemini_response(prompt, st.session_state['messages']):
                full_response += response.text
                message_placeholder.markdown(full_response)
        message_placeholder.markdown(full_response)

    
    st.session_state['messages'].append({"role": "user", "content": prompt})
    st.session_state['messages'].append({"role": "assistant", "content": full_response})
    save_message(st.session_state['current_chat_id'], "user", prompt) 
    save_message(st.session_state['current_chat_id'], "assistant", full_response)  