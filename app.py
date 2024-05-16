# Load api keys (using environment variables)
from dotenv import load_dotenv
load_dotenv()
import asyncio
import time

# Main imports
from langchain_openai import ChatOpenAI  # Interact with OpenAI API
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # Build chat prompts
from langchain.agents import create_openai_functions_agent, AgentExecutor  # Create chat agents
from langchain_community.tools.tavily_search import TavilySearchResults  # Search functionality
from langchain.memory import ConversationBufferMemory  # Manage conversation history
from langchain_community.chat_message_histories.upstash_redis import UpstashRedisChatMessageHistory

import streamlit as st  # Streamlit web framework
from streamlit_option_menu import option_menu  # Sidebar menu for options

UPSTASH_URL = "https://endless-cub-49409.upstash.io"
UPSTASH_REDIS_REST_TOKEN = "AcEBAAIncDFmMWNhZTc4MmVmYWI0OTMxYjk0Y2JhZDU4ZTgxNGUzOHAxNDk0MDk"

# Long memory (uses Upstash redis for conversation history, commented out)
def long_memory(db_name):
    history = UpstashRedisChatMessageHistory(
        url=UPSTASH_URL,
        token=UPSTASH_REDIS_REST_TOKEN,
        session_id=db_name
    )

    return history

def clear_long_memory(db_name):
    history = long_memory(db_name)  # Fetch the history object for the database
    history.clear() 

# Create agentExecutor (modified to run only once per emotion)
def create_agentExecutor(msg, db_name):
    if db_name not in st.session_state:  # Check if agent for this name exists
        model = ChatOpenAI(
            model="gpt-3.5-turbo-1106",
            temperature=0.4
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a {msg}"),  # Define persona in the prompt
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        search = TavilySearchResults()
        tools = [search]

        agent = create_openai_functions_agent(
            llm=model,
            prompt=prompt,
            tools=tools
        )

        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=long_memory(db_name)  # Conversation history (commented out)
        )

        agentExecutor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory
        )

        st.session_state[db_name] = agentExecutor  # Store agent under its name
    else:
        agentExecutor = st.session_state[db_name]  # Retrieve existing agent

    return agentExecutor

# Process chat (sends user input to the agent and gets response)
def process_chat(agentExecutor, input):
    response = agentExecutor.invoke({
        "input": input
    })
    return response["output"]

# Stream chat (handles chat history, user input, and displaying responses)
def stream_chat(msg):
    current_emotion = st.session_state.get("current_emotion")

    history = long_memory(current_emotion)  # Fetch chat history from Redis
    chat_history = asyncio.run(history.aget_messages())  # Correctly await the coroutine

    for n,i in enumerate(chat_history):
        if n%2 == 0:
            with st.chat_message("User"):
                st.markdown(i.content)
        else:
            with st.chat_message("Ai"):
                st.markdown(i.content)

    if prompt := st.chat_input(msg):
        with st.chat_message("User"):
            st.markdown(prompt)
        st.session_state.conversations[current_emotion].append({"role": "User", "content": prompt})

        with st.spinner("AI is responding..."):  # Add a loading spinner
            response = process_chat(st.session_state.age, prompt)

        with st.chat_message("Ai"):
            st.markdown(response)
        st.session_state.conversations[current_emotion].append({"role": "Ai", "content": response})


# Set agent (creates a new agentExecutor for the chosen persona)
def set_age(details, db):
    if db != st.session_state.get("current_emotion", None):  # Check if emotion changed
        st.session_state.current_emotion = db # Update current emotion

    st.session_state.age = create_agentExecutor(details, db)

# Main section
if __name__ == "__main__":

    # Emotional states for the AI
    opt = ["Default", "Angry", "Happy", "Sad", "Fear"]

    if "conversations" not in st.session_state:
        st.session_state.conversations = {
            "default": [],  # Conversation history for default emotion
            "angry": [],    # Conversation history for angry emotion
            "happy" : [],
            "sad" : [],
            "fear" : []
        }

    if "age" not in st.session_state:
        st.session_state.age = create_agentExecutor("ai", "default")  # Create default agent

    # Sidebar menu for choosing emotion
    with st.sidebar:
        selected = option_menu(
                menu_title="Choose Emotion",
                options=opt
        )

    # Sidebar menu...
    if st.sidebar.button("Clear All Data"):
        loading_message = st.empty()  # Placeholder for loading message
        loading_message.text("Deleting data...")  # Initial message

        # Clear all data logic with progress update
        with st.spinner("Clearing session state..."):
            st.session_state.clear()
            with st.spinner("Clearing long memory..."):
                for emotion in ["default", "angry", "happy", "sad", "fear"]:
                    clear_long_memory(emotion)
                    loading_message.text(f"Clearing data for {emotion}...")  # Update message
                loading_message.empty()  # Remove message after deletion

    # Handle selections based on chosen emotion
    if selected == "Default":
        st.title("DEFAULT AI")
        my_bar = st.progress(0)
        for percent_complete in range(100):
            my_bar.progress(percent_complete + 1)
            time.sleep(0.01)
        set_age("ai", "default")  # Create/reuse default agent
        stream_chat("Ask me anything")  # Start chat with default persona

    if selected == "Angry":
        st.title("ANGRY AI")
        my_bar = st.progress(0)
        for percent_complete in range(100):
            my_bar.progress(percent_complete + 1)
            time.sleep(0.01)
        set_age("angry ai. You are always very busy and do not want to help. You answer every question in a very angry tone. You try to abuse the user all the time", "angry")
        stream_chat("What do you want stupid")  # Start chat with angry persona

    if selected == "Happy":
        st.title("HAPPY AI")
        my_bar = st.progress(0)
        for percent_complete in range(100):
            my_bar.progress(percent_complete + 1)
            time.sleep(0.01)
        set_age("happy ai. You are always very happy and excited. You answer every question with extream excitement. You try to make user happy all the time","happy")
        stream_chat("anything you want...")  # Start chat with happy persona

    if selected == "Sad":
        st.title("SAD AI")
        my_bar = st.progress(0)
        for percent_complete in range(100):
            my_bar.progress(percent_complete + 1)
            time.sleep(0.01)
        set_age("You are a sad AI. You are extreamly depressed all the time and talk about death and other stuff all the time","sad")
        stream_chat("sad things...")  # Start chat with sad persona

    if selected == "Fear":
        st.title("FEAR AI")
        my_bar = st.progress(0)
        for percent_complete in range(100):
            my_bar.progress(percent_complete + 1)
            time.sleep(0.01)
        set_age("You are a fearful AI. You are constantly that something bad will happen","fear")
        stream_chat("too scary...")  # Start chat with fearful persona

