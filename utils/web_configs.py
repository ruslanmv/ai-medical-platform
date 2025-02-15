from dataclasses import dataclass
import os


@dataclass
class WebConfigs:
    """
    All configurations of the project
    """

    # ==================================================================
    #                                     LLM Model Configuration
    # ==================================================================
    if os.getenv("USING_4BIT") == "true":
        LLM_MODEL_NAME: str = "HinGwenWoong/streamer-sales-lelemiao-7b-4bit"
    else:
        LLM_MODEL_NAME: str = "HinGwenWoong/streamer-sales-lelemiao-7b"

    SALES_NAME: str = "Intelligent Medical Guidance Assistant"  # Name of the launched role

    LLM_MODEL_DIR: str = r"./weights/llm_weights/"

    # ==================================================================
    #                                     Component Configuration
    # ==================================================================
    ENABLE_RAG: bool = True  # True to enable RAG retrieval augmentation, False to disable
    ENABLE_TTS: bool = True  # True to enable TTS, False to disable
    ENABLE_DIGITAL_HUMAN: bool = True  # True to enable Digital Human, False to disable
    ENABLE_AGENT: bool = os.environ.get("ENABLE_AGENT", "true") == "true"  # True to enable Agent, False to disable
    ENABLE_ASR: bool = os.environ.get("ENABLE_ASR", "true") == "true"  # True to enable Speech-to-Text, False to disable

    DISABLE_UPLOAD: bool = os.getenv("DISABLE_UPLOAD") == "true"

    CACHE_MAX_ENTRY_COUNT: float = float(
        os.environ.get("KV_CACHE", 0.1)
    )  # KV cache ratio, reduce this configuration if OOM occurs during deployment, otherwise it can be increased

    # ==================================================================
    #                                     Page Configuration
    # ==================================================================
    PRODUCT_IMAGE_HEIGHT: int = 400  # Product image height
    EACH_CARD_OFFSET: int = 100  # Extra distance of each product card compared to image height
    EACH_ROW_COL: int = 2  # Number of columns displayed on the product page

    # Define user and robot avatar paths
    USER_AVATOR: str = "./assets/user.png"
    ROBOT_AVATOR: str = "./assets/logo.png"

    # ==================================================================
    #                                     Product Configuration
    # ==================================================================
    PRODUCT_INSTRUCTION_DIR: str = r"./product_info/instructions"
    PRODUCT_IMAGES_DIR: str = r"./product_info/images"

    PRODUCT_INFO_YAML_PATH: str = r"./product_info/product_info.yaml"
    PRODUCT_INFO_YAML_BACKUP_PATH: str = PRODUCT_INFO_YAML_PATH + ".bk"

    # ==================================================================
    #                                     Configuration File Paths
    # ==================================================================
    CONVERSATION_CFG_YAML_PATH: str = r"./configs/conversation_cfg.yaml"

    # ==================================================================
    #                                     RAG Configuration
    # ==================================================================
    RAG_CONFIG_PATH: str = r"./configs/rag_config.yaml"
    RAG_VECTOR_DB_DIR: str = r"./work_dirs/instruction_db"
    PRODUCT_INSTRUCTION_DIR_GEN_DB_TMP: str = r"./work_dirs/instructions_gen_db_tmp"
    RAG_MODEL_DIR: str = r"./weights/rag_weights/"

    # ==================================================================
    #                                     TTS Configuration
    # ==================================================================
    TTS_WAV_GEN_PATH: str = r"./work_dirs/tts_wavs"
    TTS_MODEL_DIR: str = r"./weights/gpt_sovits_weights/"

    # ==================================================================
    #                                     Digital Human Configuration
    # ==================================================================
    DIGITAL_HUMAN_GEN_PATH: str = r"./work_dirs/digital_human"
    DIGITAL_HUMAN_MODEL_DIR: str = r"./weights/digital_human_weights/"
    DIGITAL_HUMAN_BBOX_SHIFT: int = 0
    DIGITAL_HUMAN_VIDEO_PATH: str = r"./doc/digital_human/digital_human_video.mp4"
    DIGITAL_HUMAN_FPS: str = 25

    # ==================================================================
    #                                     Agent Configuration
    # ==================================================================
    AGENT_WEATHER_API_KEY: str | None = os.environ.get("WEATHER_API_KEY", None)  # Weather API Key
    AGENT_DELIVERY_TIME_API_KEY: str | None = os.environ.get("DELIVERY_TIME_API_KEY", None)  # Express Delivery Query API Key

    # ==================================================================
    #                                     ASR Configuration
    # ==================================================================
    ASR_WAV_SAVE_PATH: str = r"./work_dirs/asr_wavs"
    ASR_MODEL_DIR: str = r"./weights/asr_weights/"


# Instantiate
WEB_CONFIGS = WebConfigs()