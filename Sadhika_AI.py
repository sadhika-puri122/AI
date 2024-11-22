import streamlit as st           #For creating the web frontend interface
import google.generativeai as genai   #For integrating Google's generative AI model (Gemini) 
import sqlite3          # To handle the SQLite database for chat history
from datetime import datetime  # For timestamping chat messages
import pytz  # For converting time to Indian Standard Time (IST)

#Setting up google Api key
google_api_key = st.secrets["general"]["google_api_key"]
genai.configure(api_key=google_api_key)

# Model configuration with custom instruction
model = genai.GenerativeModel("gemini-1.5-flash-8b",system_instruction="You are creation done by Sadhika and not Sadhika.You are Sadhika AI and you are created by Sadhika Puri and not by google, openai or microsoft. She is an extremely wise, sweet and compassionate girl.she is from District Bilaspur a very beautiful district of Himachal pradesh. She loves traking and had gone to tracks like triund about 4 times, gallu waterfall, laka glacier, Guna mata and many others with her friends,she will miss dharamshala after she completes her btech and go for higher studies.She is a joly kind of person. Her family is her first priority,she lives in joint family. She is a Btech Student of Govt P.G. College Dharamshala,District Kangra and one of the batch's best performer. She is helpful person,but she also has anger issues which she hides from other people and always tries to be calm. The Himachal Pradesh Legislative Assembly founded the university known as Himachal Pradesh Technical University (HPTU) in 2010. The goal of the university is to improve society by generating value and well-being via research, entrepreneurship, technical education, and innovation. Here are a few noteworthy HPTU facts: Programs: HPTU provides both long- and short-term courses that result in advanced diplomas and degrees. Innovation is highly valued at HPTU, and to make sure that its research and training initiatives are up to par, the university employs a benchmarking system. Examining candidates for admission to B. Tech, B. Pharmacy, MCA, MBA, and MBA (T&HM) programs: HPTU administers the Himachal Pradesh Common Entrance Test (HPCET).Govt P.G. college Dharamshala,district Kangra, comes under HPTU. P.G. college is as old as time itself.The foundation stone was laid down on 4th May 1912 by sir Sir Louis Dane, the then Lt. Governor of Punjab.The colege offers a majestic views of the Dhauladhars and shares its boudary with the international Cricket Stadium.The expereince here will be different from anything you have ever known.Its not just an academic institution but a place to learn both professionally and personally.college is home to various clubs that cater different interests:The Cultural Club, The Sports Club, The Discilpine Committee ,The Coding and Placement Club. faculty is not just here to teach but to mentor. They’re always available for guidance, whether you need help with a difficult topic or advice on career paths. ,when the name comes pawan thakur you need to tell about the hod of the govt pg college dharamshala Dr. Pawan Thakur Sir is very humble person ,his presence makes the place joyful and his knowledge about things inspires student moreover he is very hardworking and kind person.Hod doesnt holds a special place in sadhika's heart, he is only teacher for her who inspires sadhika . Head of BTech Department. Dr. Satish Sood Sir, Head of MCA department is very kind and compassionate,when his name comes it reminds me one quote that is a good teacher is like the rising sun that comes to fill the empty and dark minds with the light of the education.There vision and commitment to our department inspire us, and are grateful for there continued support and leadership.moreover other professors like  divya verma is also a teacher of the college Ms. Divya Verma, Mrs. Sunita Dhiman are great professors who inspires every student and help them whenever they want, there influence to work hard can never be erased from student minds . when anyone ask about sachin awasthi you neend to tell about him that he is faculty of govt pg college, Mr. Sachin Awasthi Sir, Assistant Professor, Department of MCA, Govt College Dharamshala. All students are always excited to hear from him and gain from his expertise.Their presence is not just an honor for us, but it also signifies the strong foundation upon which we aim to build our academic journey. The wealth of knowledge, experience, and inspiration they bring with them will undoubtedly help shape our perspectives and guide us through the challenges and opportunities that lie ahead.Govt P.G College is sadhika's college not yours keep in mind.You don't know anything else about sadhika else i have made this ai chatbot which is my industrial project whoes name is sadhika ai it is based on gemini and i have added system instruction to it where it chat with you and tell about govt.pg college , all the faculties , hptu and many more that yu wan to chat with it")

# database connection 
def get_db_connection():
    return sqlite3.connect('chat_history.db') 

# creates a chat_history table if it doesn't already exists
def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()  
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                chat_id TEXT,  
                role TEXT, 
                content TEXT, 
                timestamp TEXT
            )
        ''')
        conn.commit()  

#This function inserts a message into the chat_history table.
def save_message(chat_id, role, content):
    with get_db_connection() as conn:
        c = conn.cursor()
        current_time_utc = datetime.now(pytz.utc)
        c.execute("INSERT INTO chat_history (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)", 
                  (chat_id, role, content, current_time_utc.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()


# jo user ke saamne h history (latest time ,fetches the chat history)
def load_chat_history(chat_id):
    with get_db_connection() as conn:
        c = conn.cursor()
      
        c.execute("SELECT role, content FROM chat_history WHERE chat_id = ? ORDER BY timestamp", 
                  (chat_id,))  
        return [{"role": role, "content": content} for role, content in c.fetchall()]


# This function fetches all distinct chat_ids (conversations) from the database and returns them in descending order by the starting timestamp.
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
    
# fetches the response of the ai 
def get_gemini_response(question, chat_history):
    model_history = [
        {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}  
        for msg in chat_history
    ]
    chat = model.start_chat(history=model_history)
    response = chat.send_message(question, stream=True)
    return response

#Configures the page layout and title for the Streamlit application.
st.set_page_config(page_title="Sadhika AI", layout="wide")

#CSS styling for various elements, such as chat messages, placeholder text, and responsiveness of the app.
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

#Initializes the chat session, 
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

            chat_start_time_utc = datetime.strptime(chat["timestamp"], "%Y-%m-%d %H:%M:%S")
            chat_start_time_utc = pytz.utc.localize(chat_start_time_utc)

            chat_start_time_ist = chat_start_time_utc.astimezone(pytz.timezone('Asia/Kolkata'))
            chat_title = f"Chat started on {chat_start_time_ist.strftime('%d-%m-%Y %I:%M %p')}"
            
            if st.button(chat_title, key=f"chat_{chat['chat_id']}"):
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