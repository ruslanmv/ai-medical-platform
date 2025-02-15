#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time     : 2024.4.16


import copy
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

from utils.web_configs import WEB_CONFIGS

# Initialize Streamlit page configuration
st.set_page_config(
    page_title="Intelligent Medical Guidance",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/nhbdgtgefr/Intelligent-Medical-Guidance-Large-Model/tree/main",
        "About": "# Intelligent Medical Guidance Large Model",
    },
)
from utils.rag.rag_worker import gen_rag_db
from utils.tools import resize_image

from utils.model_loader import RAG_RETRIEVER  # isort:skip


@st.experimental_dialog("Department Introduction", width="large")
def instruction_dialog(instruction_path):
    """
    Display the instruction manual popup window.

    Displays the content of the manual file in markdown format in the Streamlit application,
    and provides an "OK" button for the user to confirm reading.

    Args:
        instruction_path (str): The file path of the instruction manual, which should be a text file and encoded in utf-8.
    """
    print(f"Show instruction : {instruction_path}")
    with open(instruction_path, "r", encoding="utf-8") as f:
        instruct_lines = "".join(f.readlines())

    # st.warning("Be sure to click the [OK] button below to leave this page", icon="⚠️")
    st.markdown(instruct_lines)
    # st.warning("Be sure to click the [OK] button below to leave this page", icon="⚠️")
    if st.button("OK"):
        st.rerun()


def on_btton_click(*args, **kwargs):
    """
    Callback function for button click events.
    """

    # Execute corresponding operations based on the button type
    if kwargs["type"] == "check_instruction":
        # Display instruction manual
        st.session_state.show_instruction_path = kwargs["instruction_path"]

    elif kwargs["type"] == "process_sales":
        # Switch to the department introduction page
        st.session_state.page_switch = "pages/selling_page.py"

        # Update product information in session state
        st.session_state.hightlight = kwargs["heighlights"]
        product_info_struct = copy.deepcopy(st.session_state.product_info_struct_template)
        product_info_str = product_info_struct[0].replace("{name}", kwargs["product_name"])
        product_info_str += product_info_struct[1].replace("{highlights}", st.session_state.hightlight)

        # Generate product copywriting prompt
        st.session_state.first_input = copy.deepcopy(st.session_state.first_input_template).replace(
            "{product_info}", product_info_str
        )

        # Update image path and product name
        st.session_state.image_path = kwargs["image_path"]
        st.session_state.product_name = kwargs["product_name"]

        # Update departure place, express company name
        # st.session_state.departure_place = kwargs["departure_place"]
        # st.session_state.delivery_company_name = kwargs["delivery_company_name"]

        # Set to default digital human video path
        st.session_state.digital_human_video_path = WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_PATH

        # # Clear voice
        # if ENABLE_TTS:
        #     for message in st.session_state.messages:
        #         if "wav" not in message:
        #             continue
        #         Path(message["wav"]).unlink()

        # Clear historical dialogue
        st.session_state.messages = []


def make_product_container(product_name, product_info, image_height, each_card_offset):
    """
    Create and display product information containers.

    Parameters:
    - product_name: Product name.
    - product_info: Dictionary containing product information, including image path, features, and instruction manual path.
    - image_height: Height of the image display area.
    - each_card_offset: Spacing between parts within the container.
    """

    # Create a product information container with a border, set height
    with st.container(border=True, height=image_height + each_card_offset):

        # Page title
        st.header(product_name)

        # Divide into left and right columns, left for image, right for product information
        image_col, info_col = st.columns([0.2, 0.8])

        # Image display area
        with image_col:
            # print(f"Loading {product_info['images']} ...")
            image = resize_image(product_info["images"], max_height=image_height)
            st.image(image, channels="bgr")

        # Product information display area
        with info_col:

            # Instruction manual button
            st.subheader("Department Introduction", divider="grey")
            st.button(
                "View",
                key=f"check_instruction_{product_name}",
                on_click=on_btton_click,
                kwargs={
                    "type": "check_instruction",
                    "product_name": product_name,
                    "instruction_path": product_info["instruction"],
                },
            )

            # Main information display
            st.subheader("Main Doctors", divider="grey")

            heighlights_str = "、".join(product_info["heighlights"])
            st.text(heighlights_str)

            
            # st.button("Update", key=f"update_manual_{product_name}")

            # Guidance button
            st.subheader("AI Guidance Assistant", divider="grey")
            st.button(
                "Start Guidance",
                key=f"process_sales_{product_name}",
                on_click=on_btton_click,
                kwargs={
                    "type": "process_sales",
                    "product_name": product_name,
                    "heighlights": heighlights_str,
                    "image_path": product_info["images"],
                    # "departure_place": product_info["departure_place"],
                    # "delivery_company_name": product_info["delivery_company_name"],
                },
            )


def delete_old_files(directory, limit_time_s=60 * 60 * 5):
    """
    Delete files in the specified directory that exceed a certain time.

    :param directory: Directory path to check and delete files
    """
    # Get current timestamp
    current_time = time.time()

    # Traverse all files and subdirectories in the directory
    for file_path in Path(directory).iterdir():

        # Get file modification timestamp
        file_mtime = os.path.getmtime(file_path)

        # Calculate file age (in seconds)
        file_age_seconds = current_time - file_mtime

        # Check if the file is older than n seconds
        if file_age_seconds > limit_time_s:
            try:

                if file_path.is_dir():
                    shutil.rmtree(file_path)
                    continue

                # Delete file
                file_path.unlink()
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")


def get_sales_info():
    """
    Load sales-related information from the configuration file and store it in the session state.

    This function does not accept parameters and does not directly return any value, but updates the global session state, including:
    - sales_info: System greeting, customized for the sales role
    - first_input_template: The first input template at the start of the conversation
    - product_info_struct_template: Product information structure template
    """

    # Load dialogue configuration file
    with open(WEB_CONFIGS.CONVERSATION_CFG_YAML_PATH, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    role_type_data = dataset_yaml.get("role_type", {})
    if WEB_CONFIGS.SALES_NAME in role_type_data:
        sales_info = role_type_data[WEB_CONFIGS.SALES_NAME]
    else:
        print(f"Key '{WEB_CONFIGS.SALES_NAME}' does not exist in 'role_type'")
        sales_info = None  # Or assign a default value

    # Extract role information from configuration
    sales_info = dataset_yaml["role_type"][WEB_CONFIGS.SALES_NAME]

    # Extract conversation setting related information from configuration
    system = dataset_yaml["conversation_setting"]["system"]
    first_input = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct = dataset_yaml["product_info_struct"]

    # Insert sales role name and role information into system prompt
    system_str = system.replace("{role_type}", WEB_CONFIGS.SALES_NAME).replace("{character}", "、".join(sales_info))

    # Update session state, store sales related information
    st.session_state.sales_info = system_str
    st.session_state.first_input_template = first_input
    st.session_state.product_info_struct_template = product_info_struct


def init_product_info():
    # Read yaml file
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # Sort according to ID to avoid disorder
    product_info_dict = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["id"]))

    product_name_list = list(product_info_dict.keys())

    # Generate product information
    for row_id in range(0, len(product_name_list), WEB_CONFIGS.EACH_ROW_COL):
        for col_id, col_handler in enumerate(st.columns(WEB_CONFIGS.EACH_ROW_COL)):
            with col_handler:
                if row_id + col_id >= len(product_name_list):
                    continue

                product_name = product_name_list[row_id + col_id]
                make_product_container(
                    product_name, product_info_dict[product_name], WEB_CONFIGS.PRODUCT_IMAGE_HEIGHT, WEB_CONFIGS.EACH_CARD_OFFSET
                )

    return len(product_name_list)


def init_tts():
    # TTS initialization
    if "gen_tts_checkbox" not in st.session_state:
        st.session_state.gen_tts_checkbox = WEB_CONFIGS.ENABLE_TTS
    if WEB_CONFIGS.ENABLE_TTS:
        # Clear all voice files older than 1 hour
        Path(WEB_CONFIGS.TTS_WAV_GEN_PATH).mkdir(parents=True, exist_ok=True)
        delete_old_files(WEB_CONFIGS.TTS_WAV_GEN_PATH)


def init_digital_human():
    # Digital human initialization
    if "digital_human_video_path" not in st.session_state:
        st.session_state.digital_human_video_path = WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_PATH
    if "gen_digital_human_checkbox" not in st.session_state:
        st.session_state.gen_digital_human_checkbox = WEB_CONFIGS.ENABLE_DIGITAL_HUMAN

    if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
        # Clear all video files older than 1 hour
        Path(WEB_CONFIGS.DIGITAL_HUMAN_GEN_PATH).mkdir(parents=True, exist_ok=True)
        # delete_old_files(st.session_state.digital_human_root)


def init_asr():
    # Clear old ASR files
    if WEB_CONFIGS.ENABLE_ASR and Path(WEB_CONFIGS.ASR_WAV_SAVE_PATH).exists():
        delete_old_files(WEB_CONFIGS.ASR_WAV_SAVE_PATH)

    st.session_state.asr_text_cache = ""


def main():
    """
    Initialize page configuration, load models, handle page switching, and display product information.
    """
    print("Starting...")

    # Initialize page switching
    if "page_switch" not in st.session_state:
        st.session_state.page_switch = "app.py"
    st.session_state.current_page = "app.py"

    # Display product instruction manual
    if "show_instruction_path" not in st.session_state:
        st.session_state.show_instruction_path = "X-X"
    if st.session_state.show_instruction_path != "X-X":
        instruction_dialog(st.session_state.show_instruction_path)
        st.session_state.show_instruction_path = "X-X"

    # Check if page switching is needed
    if st.session_state.page_switch != st.session_state.current_page:
        st.switch_page(st.session_state.page_switch)

    # TTS initialization
    init_tts()

    # Digital human initialization
    init_digital_human()

    # ASR initialization
    init_asr()

    if "enable_agent_checkbox" not in st.session_state:
        st.session_state.enable_agent_checkbox = WEB_CONFIGS.ENABLE_AGENT

        if WEB_CONFIGS.AGENT_DELIVERY_TIME_API_KEY is None or WEB_CONFIGS.AGENT_WEATHER_API_KEY is None:
            WEB_CONFIGS.ENABLE_AGENT = False
            st.session_state.enable_agent_checkbox = False

    # Get sales information
    if "sales_info" not in st.session_state:
        get_sales_info()


    # Homepage title

    st.title("Intelligent Medical Guidance Large Model")
    # st.header("Product Page")
    # Description
    st.info(
        "This is the assistant backend. Here is the directory of department information for the assistant to explain. Select a department and click [Start Guidance] to jump to the assistant guidance page. If you need to add more information, click the add button below.",
        icon="ℹ️",
    )

    # Initialize product list
    product_num = init_product_info()

    # Sidebar displays product quantity, stationed brand owners
    with st.sidebar:
        # Title
        st.header("Intelligent Medical Guidance Large Model", divider="grey")
        st.markdown("[Intelligent Medical Guidance Large Model](https://github.com/nhbdgtgefr/item)")

        
        st.subheader(f"Assistant Backend Information", divider="grey")
        st.markdown(f"Total Departments: {product_num} Departments")

        # TODO Single product transaction volume
        # st.markdown(f"Total Brand Owners: {len(product_name_list)} 个")

        if WEB_CONFIGS.ENABLE_TTS:
            # Whether to generate TTS
            st.subheader(f"TTS Configuration", divider="grey")
            st.session_state.gen_tts_checkbox = st.toggle("Generate Voice", value=st.session_state.gen_tts_checkbox)

        if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
            # Whether to generate Digital Human
            st.subheader(f"Digital Human Configuration", divider="grey")
            st.session_state.gen_digital_human_checkbox = st.toggle(
                "Generate Digital Human Video", value=st.session_state.gen_digital_human_checkbox
            )

        # if WEB_CONFIGS.ENABLE_AGENT:
        #     # Whether to use agent
        #     # st.subheader(f"Agent Configuration", divider="grey")
        #     # with st.container(border=True):
        #         # st.markdown("**Plugin List**")
        #         # st.button("Combine weather to query arrival time", type="primary")
        #     # st.session_state.enable_agent_checkbox = st.toggle("Use Agent Capability", value=st.session_state.enable_agent_checkbox)

    # Add new product upload form
    with st.form(key="add_product_form"):
        product_name_input = st.text_input(label="Add Department Name")
        heightlight_input = st.text_input(label="Add Department Doctors, separated by '、'")
        # departure_place_input = st.text_input(label="Departure Place")
        # delivery_company_input = st.text_input(label="Express Company Name")
        product_image = st.file_uploader(label="Upload Department Image", type=["png", "jpg", "jpeg", "bmp"])
        product_instruction = st.file_uploader(label="Upload Department Instruction Manual", type=["md"])
        submit_button = st.form_submit_button(label="Submit", disabled=WEB_CONFIGS.DISABLE_UPLOAD)

        if WEB_CONFIGS.DISABLE_UPLOAD:
            st.info(
                "The code on Github already supports the logic of uploading new information.\nHowever, because the open Web APP does not have a new information review mechanism, uploading information is temporarily not enabled here.\nYou can clone this project to your machine and start it to enable the upload button",
                icon="ℹ️",
            )

        if submit_button:
            update_product_info(
                product_name_input,
                heightlight_input,
                product_image,
                product_instruction,
                # departure_place_input,
                # delivery_company_input,
            )


def update_product_info(
    product_name_input, heightlight_input, product_image, product_instruction
):
    """
    Function to update product information.

    Parameters:
    - product_name_input: Product name input, string type.
    - heightlight_input: Product features input, string type.
    - product_image: Product image, image type.
    - product_instruction: Product instruction manual, text type.
    - departure_place: Departure place.
    - delivery_company: Express company.

    Returns:
    None. This function directly manipulates the UI state and does not return any value.
    """

    # TODO Image and features can be left blank, and the large model automatically generates a version for users to choose from

    # Check input parameters
    if product_name_input == "" or heightlight_input == "":
        st.error("Department name and main doctor cannot be empty")
        return

    if product_image is None or product_instruction is None:
        st.error("Image and department introduction cannot be empty")
        return

    # if departure_place == "" or delivery_company == "":
    #     st.error("Departure place and express company name cannot be empty")
    #     return

    # Display upload status and perform upload operations
    with st.status("Uploading...", expanded=True) as status:

        save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        image_save_path = Path(WEB_CONFIGS.PRODUCT_IMAGES_DIR).joinpath(f"{save_tag}{Path(product_image.name).suffix}")
        instruct_save_path = Path(WEB_CONFIGS.PRODUCT_INSTRUCTION_DIR).joinpath(
            f"{save_tag}{Path(product_instruction.name).suffix}"
        )

        st.write("Saving image...")
        with open(image_save_path, "wb") as file:
            file.write(product_image.getvalue())

        st.write("Saving department introduction...")
        with open(instruct_save_path, "wb") as file:
            file.write(product_instruction.getvalue())

        st.write("Updating department details...")
        with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
            product_info_dict = yaml.safe_load(f)

        # Sort to prevent disorder
        product_info_dict = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["id"]))
        max_id_key = max(product_info_dict, key=lambda x: product_info_dict[x]["id"])

        product_info_dict.update(
            {
                product_name_input: {
                    "heighlights": heightlight_input.split("、"),
                    "images": str(image_save_path),
                    "instruction": str(instruct_save_path),
                    "id": product_info_dict[max_id_key]["id"] + 1,
                    # "departure_place": departure_place,
                    # "delivery_company_name": delivery_company,
                }
            }
        )

        # Backup
        if Path(WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH).exists():
            Path(WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH).unlink()
        shutil.copy(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH)

        # Overwrite save
        with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(product_info_dict, f, allow_unicode=True)

        st.write("Generating database...")
        if WEB_CONFIGS.ENABLE_RAG:
            # Regenerate RAG vector database
            gen_rag_db(force_gen=True)

            # Reload retriever
            RAG_RETRIEVER.pop("default")
            RAG_RETRIEVER.get(fs_id="default", config_path=WEB_CONFIGS.RAG_CONFIG_PATH, work_dir=WEB_CONFIGS.RAG_VECTOR_DB_DIR)

        # Update status
        status.update(label="Department information added successfully!", state="complete", expanded=False)

        st.toast("Information added successfully!", icon="🎉")

        with st.spinner("Preparing to refresh the page..."):
            time.sleep(3)

        # Refresh page
        st.rerun()


if __name__ == "__main__":
    # streamlit run app.py --server.address=0.0.0.0 --server.port 7860

    # print("Starting...")
    main()