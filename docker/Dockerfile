FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-devel

LABEL MAINTAINER="HinGwen.Wong"

# Set timezone
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo 'Asia/Shanghai' > /etc/timezone

# Switch to Alibaba Cloud mirror and install necessary system libraries
RUN sed -i s/archive.ubuntu.com/mirrors.aliyun.com/g /etc/apt/sources.list \
    && sed -i s/security.ubuntu.com/mirrors.aliyun.com/g /etc/apt/sources.list \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends wget git libgl1 libglib2.0-0 unzip libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /workspace/Streamer-Sales
WORKDIR /workspace/Streamer-Sales

ENV HF_ENDPOINT="https://hf-mirror.com"
ENV LANG="en_US.UTF-8"

# Install necessary dependency environment
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt