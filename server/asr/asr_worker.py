import datetime

from funasr import AutoModel
from funasr.download.name_maps_from_hub import name_maps_ms as NAME_MAPS_MS
from modelscope import snapshot_download
from modelscope.utils.constant import Invoke, ThirdParty

from ..web_configs import WEB_CONFIGS


def load_asr_model():
    # Model download
    model_path_info = dict()
    for model_name in ["paraformer-zh", "fsmn-vad", "ct-punc"]:
        print(f"downloading asr model : {NAME_MAPS_MS[model_name]}")
        mode_dir = snapshot_download(
            NAME_MAPS_MS[model_name],
            revision="master",
            user_agent={Invoke.KEY: Invoke.PIPELINE, ThirdParty.KEY: "funasr"},
            cache_dir=WEB_CONFIGS.ASR_MODEL_DIR,
        )
        model_path_info[model_name] = mode_dir
        NAME_MAPS_MS[model_name] = mode_dir  # Update weight path environment variable

    print(f"ASR model path info = {model_path_info}")
    # paraformer-zh is a multi-functional asr model
    # use vad, punc, spk or not as you need
    model = AutoModel(
        model="paraformer-zh",  # Speech recognition, with timestamp output, non-real-time
        vad_model="fsmn-vad",  # Voice Activity Detection (VAD), real-time
        punc_model="ct-punc",  # Punctuation restoration
        # spk_model="cam++" # Speaker verification/diarization
        model_path=model_path_info["paraformer-zh"],
        vad_kwargs={"model_path": model_path_info["fsmn-vad"]},
        punc_kwargs={"model_path": model_path_info["ct-punc"]},
    )
    return model


def process_asr(model: AutoModel, wav_path):
    # https://github.com/modelscope/FunASR/blob/main/README_zh.md#%E5%AE%9E%E6%97%B6%E8%AF%AD%E9%9F%B3%E8%AF%86%E5%88%AB
    f_start_time = datetime.datetime.now()
    res = model.generate(input=wav_path, batch_size_s=50, hotword="魔搭")
    delta_time = datetime.datetime.now() - f_start_time

    try:
        print(f"ASR using time {delta_time}s, text: ", res[0]["text"])
        res_str = res[0]["text"]
    except Exception as e:
        print("ASR parsing failed, unable to get text")
        return ""

    return res_str