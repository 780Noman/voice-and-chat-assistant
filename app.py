
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import google.generativeai as genai
from langdetect import detect
import os

# --- Page Configuration ---
st.set_page_config(page_title="Voice Assistant", page_icon="🎙️", layout="centered")

# --- Custom CSS for Styling (Dark Theme) ---
st.markdown("""
<style>
    .stApp {
        background-color: #2e2e2e;
        color: #ffffff;
    }
    .stButton>button {
        width: 100%;
        background-color: #007bff;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    .stChatInput>div>div>textarea {
        background-color: #3e3e3e;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- Header and Introduction ---
st.title("🤖 Ur/Eng Voice Assistant")
st.markdown("Created by **Noman Amjad**")
st.markdown("---")

# --- API Key Management ---
def store_api_key():
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    with st.sidebar.form(key="api_key_form"):
        st.title("🔑 API Key")
        api_key_input = st.text_input("Enter your Gemini API key", key="gemini_key", type="password")
        submitted = st.form_submit_button("Submit")
        if submitted and api_key_input:
            st.session_state.api_key = api_key_input
            st.sidebar.success("API key stored successfully!")

# --- Generative AI Configuration ---
def configure_genai():
    try:
        genai.configure(api_key=st.session_state.api_key)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Failed to configure Generative AI: {e}")
        return None

# --- Speech Recognition ---
def record_and_recognize():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("🎙️ Listening...")
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
                with st.spinner("Recognizing your voice..."):
                    text = recognizer.recognize_google(audio, language="ur-PK")
                st.success(f"You said: {text}")
                return text
            except sr.WaitTimeoutError:
                st.warning("Listening timed out. Please try again.")
            except sr.UnknownValueError:
                st.error("Sorry, I could not understand the audio.")
            except sr.RequestError as e:
                st.error(f"Could not request results; {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    except OSError:
        st.error("Microphone not found. Voice input is not available on this device or in this environment.")
    except Exception as e:
        st.error(f"An unexpected error occurred with the microphone: {e}")
    return None

# --- AI Response Generation ---
def generate_response(model, history):
    try:
        response = model.generate_content(history)
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Sorry, I encountered an error."

# --- Text-to-Speech ---
def text_to_speech(text, lang="ur"):
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"Error in text-to-speech: {e}")
        return None

# --- Main Application Logic ---
def main():
    store_api_key()

    if not st.session_state.api_key:
        st.info("Please enter your Gemini API key in the sidebar to begin.")
        return

    model = configure_genai()
    if not model:
        return

    if "history" not in st.session_state:
        st.session_state.history = []
    if "audio_path" not in st.session_state:
        st.session_state.audio_path = None

    # --- UI Selection ---
    st.sidebar.title("Mode")
    mode = st.sidebar.radio("Choose your interaction mode:", ("Chat Mode", "Voice Mode"))

    if st.sidebar.button("Clear Chat History"):
        st.session_state.history = []
        st.session_state.audio_path = None

    # --- Display Chat History ---
    for message in st.session_state.history:
        role = "You" if message["role"] == "user" else "Assistant"
        with st.chat_message(role):
            st.markdown(message["parts"][0])

    # --- Handle Audio Playback ---
    if st.session_state.audio_path:
        with open(st.session_state.audio_path, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        os.remove(st.session_state.audio_path)
        st.session_state.audio_path = None

    # --- Mode-Specific UI ---
    if mode == "Chat Mode":
        if prompt := st.chat_input("Say something"):
            st.session_state.history.append({"role": "user", "parts": [prompt]})
            with st.spinner("Assistant is thinking..."):
                response = generate_response(model, st.session_state.history)
                st.session_state.history.append({"role": "model", "parts": [response]})
            st.rerun()

    elif mode == "Voice Mode":
        if st.button("🎤 Record Voice"):
            user_text = record_and_recognize()
            if user_text:
                st.session_state.history.append({"role": "user", "parts": [user_text]})
                with st.spinner("Assistant is thinking..."):
                    bot_response = generate_response(model, st.session_state.history)
                    st.session_state.history.append({"role": "model", "parts": [bot_response]})
                    lang = detect(bot_response)
                    st.session_state.audio_path = text_to_speech(bot_response, lang=lang)
                st.rerun()

if __name__ == "__main__":
    main()
