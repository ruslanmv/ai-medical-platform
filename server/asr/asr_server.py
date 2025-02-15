from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from loguru import logger
from pydantic import BaseModel

from ..web_configs import WEB_CONFIGS
from .asr_worker import load_asr_model, process_asr

app = FastAPI()

if WEB_CONFIGS.ENABLE_ASR:
    ASR_HANDLER = load_asr_model()
else:
    ASR_HANDLER = None


class ASRItem(BaseModel):
    user_id: int   # User ID, used to differentiate calls from different users
    request_id: str   # Request ID, used to generate TTS & Digital Human
    wav_path: str   # Path to the wav file


@app.post("/asr")
async def get_asr(asr_item: ASRItem):
    # Speech to text
    result = ""
    status = "success"
    if ASR_HANDLER is None:
        result = "ASR not enable in sever"
        status = "fail"
        logger.error(f"ASR not enable...")
    else:
        result = process_asr(ASR_HANDLER, asr_item.wav_path)
    logger.info(f"ASR res for id {asr_item.request_id}, res = {result}")

    return {"user_id": asr_item.user_id, "request_id": asr_item.request_id, "status": status, "result": result}


@app.get("/asr/check")
async def check_server():
    return {"message": "server enabled"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Callback interface for API parameter input errors

    Args:
        request (_type_): _description_
        exc (_type_): _description_

    Returns:
        _type_: _description_
    """
    logger.info(request)
    logger.info(exc)
    return PlainTextResponse(str(exc), status_code=400)