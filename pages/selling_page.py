#!/usr/bin/env python
# -*- coding: utf-8 -*-



import random
from datetime import datetime
from pathlib import Path

import streamlit as st

from utils.web_configs import WEB_CONFIGS

# Set page configuration, including title, icon, layout, and menu items
st.set_page_config(
    page_title="Intelligent Medical Guidance Large Model", # Page title
    page_icon="🛒", # Page icon
    layout="wide", # Page layout
    initial_sidebar_state="expanded", # Initial sidebar state
    menu_items={ # Menu items in the top right corner
        "Get Help": "https://github.com/nhbdgtgefr/Intelligent-Medical-Guidance-Large-Model/tree/main", # Help link
        "About": "# Intelligent Medical Guidance Large Model", # About section
    },
)

from audiorecorder import audiorecorder

from utils.asr.asr_worker import process_asr
from utils.digital_human.digital_human_worker import show_video
from utils.infer.lmdeploy_infer import get_turbomind_response
from utils.model_loader import ASR_HANDLER, LLM_MODEL, RAG_RETRIEVER
from utils.tools import resize_image


def on_btn_click(*args, **kwargs):
    """
    Function to handle button click events.
    """
    if kwargs["info"] == "清除对话历史": # If the button clicked is for clearing chat history
        st.session_state.messages = [] # Clear the chat messages in session state
    elif kwargs["info"] == "返回科室页": # If the button clicked is for returning to the department page
        st.session_state.page_switch = "app.py" # Set page switch state to app.py, which is likely the department selection page
    else: # For other button clicks
        st.session_state.button_msg = kwargs["info"] # Store the button info in session state for processing


def init_sidebar():
    """
    Initializes the sidebar interface, displaying product information and operation buttons.
    """
    asr_text = ""
    with st.sidebar:
        # Title
        st.markdown("## Intelligent Medical Guidance Large Model") # Sidebar title
        st.markdown("[Intelligent Medical Guidance Large Model](https://github.com/nhbdgtgefr/Intelligent-Medical-Guidance-Large-Model)") # Link to the project
        st.subheader("Features:", divider="grey") # Subheader for features
        # st.markdown(
        #     "1. 📜 **One-click generation of主播 copy**\n2. 🚀 KV cache + Turbomind **Inference Acceleration**\n3. 📚 RAG **Retrieval-Augmented Generation**\n4. 🔊 TTS **Text-to-Speech**\n5. 🦸 **Digital Human Generation**\n6. 🌐 **Agent Network Query**\n7. 🎙️ **ASR Speech-to-Text**"
        # ) # Commented out feature list

        st.subheader("Currently Explaining") # Subheader for current product explanation
        with st.container(height=400, border=True): # Container to hold product info
            st.subheader(st.session_state.product_name) # Display product name from session state

            image = resize_image(st.session_state.image_path, max_height=100) # Resize product image
            st.image(image, channels="bgr") # Display product image

            st.subheader("Department Features", divider="grey") # Subheader for department features
            st.markdown(st.session_state.hightlight) # Display department highlights from session state

            want_to_buy_list = [ # List of phrases indicating purchase intent
                "I plan to buy it.",
                "I'm going to get it.",
                "I've decided to buy it.",
                "I'm going to place an order.",
                "I'm going to purchase this product.",
                "I'm going to buy this.",
                "I'm going to buy this one.",
                "I'm going to buy it.",
                "I've decided to buy it.",
                "I'm going to buy it.",
                "I'm going to buy this.",
            ]
            buy_flag = st.button("Add to Information 🛒", on_click=on_btn_click, kwargs={"info": random.choice(want_to_buy_list)}) # Button to simulate adding info, uses random phrase from list

        # TODO 加入卖货信息 (TODO: Add sales information)
        # 卖出 xxx 个 (Sold xxx units)
        # 成交额 (Transaction amount)

        if WEB_CONFIGS.ENABLE_ASR: # If ASR is enabled
            Path(WEB_CONFIGS.ASR_WAV_SAVE_PATH).mkdir(parents=True, exist_ok=True) # Ensure ASR save path exists

            st.subheader(f"Voice Input", divider="grey") # Subheader for voice input
            audio = audiorecorder( # Audio recorder component
                start_prompt="Start Recording", stop_prompt="Stop Recording", pause_prompt="", show_visualizer=True, key=None
            )

            if len(audio) > 0: # If audio is recorded

                # Save recorded audio as wav file
                save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".wav" # Generate unique filename
                wav_path = str(Path(WEB_CONFIGS.ASR_WAV_SAVE_PATH).joinpath(save_tag).absolute()) # Full save path

                # st.audio(audio.export().read()) # Frontend display (Commented out frontend display of audio)
                audio.export(wav_path, format="wav")  # Save audio to wav file using pydub

                # To get audio properties, use pydub AudioSegment properties:
                # st.write(
                #     f"Frame rate: {audio.frame_rate}, Frame width: {audio.frame_width}, Duration: {audio.duration_seconds} seconds"
                # ) # Commented out audio properties display

                # Speech recognition
                asr_text = process_asr(ASR_HANDLER, wav_path) # Process audio with ASR handler

                # Delete temporary files
                # Path(wav_path).unlink() # Commented out temporary file deletion

        # Whether to generate TTS
        if WEB_CONFIGS.ENABLE_TTS: # If TTS is enabled
            st.subheader("TTS Configuration", divider="grey") # Subheader for TTS config
            st.session_state.gen_tts_checkbox = st.toggle("Generate Voice", value=st.session_state.gen_tts_checkbox) # Toggle to control TTS generation

        if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN: # If Digital Human is enabled
            # Whether to generate Digital Human
            st.subheader(f"Digital Human Configuration", divider="grey") # Subheader for Digital Human config
            st.session_state.gen_digital_human_checkbox = st.toggle(
                "Generate Digital Human Video", value=st.session_state.gen_digital_human_checkbox # Toggle for Digital Human video generation
            )

        if WEB_CONFIGS.ENABLE_AGENT: # If Agent is enabled
            # Whether to use agent
            st.subheader(f"Agent Configuration", divider="grey") # Subheader for Agent config
            with st.container(border=True): # Container for Agent related options
                st.markdown("**Plugin List**") # Markdown for Plugin List
                st.button("Combine weather to query arrival time", type="primary") # Example Agent button
            st.session_state.enable_agent_checkbox = st.toggle("Use Agent Capability", value=st.session_state.enable_agent_checkbox) # Toggle for Agent capability

        st.subheader("Page Switching", divider="grey") # Subheader for page switching
        st.button("Return to Department Page", on_click=on_btn_click, kwargs={"info": "返回科室页"}) # Button to return to department page

        st.subheader("Dialogue Settings", divider="grey") # Subheader for dialogue settings
        st.button("Clear Dialogue History", on_click=on_btn_click, kwargs={"info": "清除对话历史"}) # Button to clear dialogue history

        # 模型配置 (Model Configuration - Commented out model configuration sliders in sidebar)
        # st.markdown("## 模型配置")
        # max_length = st.slider("Max Length", min_value=8, max_value=32768, value=32768)
        # top_p = st.slider("Top P", 0.0, 1.0, 0.8, step=0.01)
        # temperature = st.slider("Temperature", 0.0, 1.0, 0.7, step=0.01)

    return asr_text # Return the ASR text result


def init_message_block(meta_instruction, user_avator, robot_avator):
    """
    Initializes the message block, displaying chat history and product introduction if history is empty.
    """

    # Display chat history messages when the app reruns
    for message in st.session_state.messages: # Loop through messages in session state
        with st.chat_message(message["role"], avatar=message.get("avatar")): # Use chat_message container to format messages
            st.markdown(message["content"]) # Display message content in markdown format

            if message.get("wav") is not None: # If the message contains a wav file path
                # Display audio
                print(f"Load wav {message['wav']}") # Print loading wav info
                with open(message["wav"], "rb") as f_wav: # Open wav file in binary read mode
                    audio_bytes = f_wav.read() # Read wav file bytes
                st.audio(audio_bytes, format="audio/wav") # Display audio player in streamlit

    # If chat history is empty, display product introduction
    if len(st.session_state.messages) == 0: # Check if message history is empty
        # Direct product introduction
        get_turbomind_response( # Function to get LLM response
            st.session_state.first_input, # Initial input prompt from session state
            meta_instruction, # Meta instruction for the LLM
            user_avator, # User avatar image path
            robot_avator, # Robot avatar image path
            LLM_MODEL, # LLM model loaded from model_loader
            session_messages=st.session_state.messages, # Current session messages
            add_session_msg=False, # Do not add this response to session messages yet, as it's initial intro
            first_input_str="", # First input string - not needed here as it's already in session state
            enable_agent=False, # Agent capability disabled for initial intro
        )

    # Initialize button message state
    if "button_msg" not in st.session_state: # Check if button_msg is initialized
        st.session_state.button_msg = "x-x" # Initialize with a default value


def process_message(user_avator, prompt, meta_instruction, robot_avator):
    """
    Processes user message, displays it, and gets response from the LLM.
    """
    # Display user message in chat message container
    with st.chat_message("user", avatar=user_avator): # Format user message
        st.markdown(prompt) # Display user prompt

    get_turbomind_response( # Get LLM response function
        prompt, # User prompt
        meta_instruction, # Meta instruction for LLM
        user_avator, # User avatar image path
        robot_avator, # Robot avatar image path
        LLM_MODEL, # LLM model
        session_messages=st.session_state.messages, # Current chat messages
        add_session_msg=True, # Add this response to session messages
        first_input_str=st.session_state.first_input, # Initial input string (for context)
        rag_retriever=RAG_RETRIEVER, # RAG retriever for enhanced generation
        product_name=st.session_state.product_name, # Product name for context
        enable_agent=st.session_state.enable_agent_checkbox, # Enable Agent capability from toggle
        # departure_place=st.session_state.departure_place, # Commented out departure place
        # delivery_company_name=st.session_state.delivery_company_name, # Commented out delivery company name
    )


def main(meta_instruction):
    """
    Main function to run the Streamlit application for the selling page.
    """

    # Check page switch status and switch if necessary
    if st.session_state.page_switch != st.session_state.current_page: # Check if page switch is requested
        st.switch_page(st.session_state.page_switch) # Switch to the requested page

    # Page title
    st.title("Intelligent Medical Guidance Large Model") # Set page title

    # Description
    st.info(
        "This project is an intelligent medical guidance large model built based on artificial intelligence in the field of text, voice, and video generation. Users are granted the freedom to use this tool to create text, voice, and video, but users should abide by local laws and use it responsibly during use. Developers are not responsible for any improper use by users.", # Information message about the project
        icon="❗", # Icon for the info message
    )

    # Initialize sidebar
    asr_text = init_sidebar() # Initialize sidebar and get ASR text input if any

    # Initialize chat history
    if "messages" not in st.session_state: # Check if messages are initialized in session state
        st.session_state.messages = [] # Initialize empty message list

    message_col = None # Initialize message column variable for layout control
    if st.session_state.gen_digital_human_checkbox and WEB_CONFIGS.ENABLE_DIGITAL_HUMAN: # If Digital Human generation is enabled

        with st.container(): # Container for layout organization
            message_col, video_col = st.columns([0.6, 0.4]) # Split layout into message and video columns

            with video_col: # In the video column
                # Create empty control
                st.session_state.video_placeholder = st.empty() # Create an empty placeholder for video
                with st.session_state.video_placeholder.container(): # Use the container of the placeholder
                    show_video(st.session_state.digital_human_video_path, autoplay=True, loop=True, muted=True) # Show digital human video

            with message_col: # In the message column
                init_message_block(meta_instruction, WEB_CONFIGS.USER_AVATOR, WEB_CONFIGS.ROBOT_AVATOR) # Initialize message block in the message column
    else: # If Digital Human is not enabled
        init_message_block(meta_instruction, WEB_CONFIGS.USER_AVATOR, WEB_CONFIGS.ROBOT_AVATOR) # Initialize message block in default layout

    # Input box display hint message
    hint_msg = "Hello, you can ask me any questions about medical consultation, and I will be happy to assist you." # Hint message for chat input
    if st.session_state.button_msg != "x-x": # Check if there's a button message to process
        prompt = st.session_state.button_msg # Use button message as prompt
        st.session_state.button_msg = "x-x" # Reset button message state
        st.chat_input(hint_msg) # Display chat input with hint message
    elif asr_text != "" and st.session_state.asr_text_cache != asr_text: # If ASR text is newly available
        prompt = asr_text # Use ASR text as prompt
        st.chat_input(hint_msg) # Display chat input with hint message
        st.session_state.asr_text_cache = asr_text # Update ASR text cache to avoid reprocessing
    else: # Default case: display empty chat input
        prompt = st.chat_input(hint_msg) # Display chat input with hint message

    # Receive user input
    if prompt: # If user has provided a prompt

        if message_col is None: # If digital human video is not enabled (default layout)
            process_message(WEB_CONFIGS.USER_AVATOR, prompt, meta_instruction, WEB_CONFIGS.ROBOT_AVATOR) # Process message in default layout
        else: # If digital human video is enabled (split layout)
            # Digital human starts, page is split into blocks, message block is in message_col
            with message_col: # Use the message column container
                process_message(WEB_CONFIGS.USER_AVATOR, prompt, meta_instruction, WEB_CONFIGS.ROBOT_AVATOR) # Process message in message column


# st.sidebar.page_link("app.py", label="商品页") # Page link to department page - commented out
# st.sidebar.page_link("./pages/selling_page.py", label="主播卖货", disabled=True) # Page link to selling page - commented out and disabled

# META_INSTRUCTION
print("into sales page") # Print statement indicating entry to sales page
st.session_state.current_page = "pages/selling_page.py" # Set current page state to selling page

if "sales_info" not in st.session_state or st.session_state.sales_info == "": # Check if sales info is initialized
    st.session_state.page_switch = "app.py" # If not, switch back to department page
    st.switch_page("app.py") # Switch to department page

main((st.session_state.sales_info)) # Run the main function with sales information from session state