#!/bin/bash

# Check the number of arguments
if [ "$#" -ne 1 ]; then
    echo "Error: Exactly one argument must be provided."
    echo "Available options are: tts, dg, asr, llm, base, or frontend."
    exit 1
fi

# Activate the virtual environment
# conda deactivate
conda activate streamer-sales

# Optional: Configure GPU settings
# export CUDA_VISIBLE_DEVICES=1

# Configure the Hugging Face domestic mirror URL
export HF_ENDPOINT="https://hf-mirror.com"

case $1 in
    tts)
        echo "Starting TTS service..."
        uvicorn server.tts.tts_server:app --host 0.0.0.0 --port 8001
        ;;

    dg)
        echo "Starting Digital Human service..."
        uvicorn server.digital_human.digital_human_server:app --host 0.0.0.0 --port 8002
        ;;

    asr)
        echo "Starting ASR service..."
        export MODELSCOPE_CACHE="./weights/asr_weights"
        uvicorn server.asr.asr_server:app --host 0.0.0.0 --port 8003
        ;;

    llm)
        echo "Starting LLM service..."
        export LMDEPLOY_USE_MODELSCOPE=True
        export MODELSCOPE_CACHE="./weights/llm_weights"
        lmdeploy serve api_server HinGwenWoong/streamer-sales-lelemiao-7b \
                                  --server-port 23333 \
                                  --model-name internlm2 \
                                  --session-len 32768 \
                                  --cache-max-entry-count 0.1 \
                                  --model-format hf
        ;;

    llm-4bit)
        echo "Starting LLM-4bit service..."
        export LMDEPLOY_USE_MODELSCOPE=True
        export MODELSCOPE_CACHE="./weights/llm_weights"
        lmdeploy serve api_server HinGwenWoong/streamer-sales-lelemiao-7b-4bit \
                                  --server-port 23333 \
                                  --model-name internlm2 \
                                  --session-len 32768 \
                                  --cache-max-entry-count 0.1 \
                                  --model-format awq
        ;;

    base)
        echo "Starting Base service..."
        # Agent Key (if available, please configure; otherwise, ignore)
        # export DELIVERY_TIME_API_KEY="${Express EBusinessID},${Express api_key}"
        # export WEATHER_API_KEY="${Weather API key}"
        uvicorn server.base.base_server:app --host 0.0.0.0 --port 8000
        ;;

    frontend)
        echo "Starting Frontend service..."
        cd frontend
        # npm install
        npm run dev
        ;;

    *)
        echo "Error: Unsupported parameter '$1'."
        echo "Available options are: tts, dg, asr, llm, llm-4bit, base, or frontend."
        exit 1
        ;;
esac

exit 0
