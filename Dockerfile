# 使用 Python 3.10 官方镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（增加构建工具）
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    build-essential \
    cmake \
    git \ 
    && rm -rf /var/lib/apt/lists/*

# 复制文件（保持原有结构）
COPY requirements.txt .
COPY detectron2-main.zip /tmp/

# 安装步骤分解（便于调试）
RUN pip install -r requirements.txt

# 安装detectron2（增加详细日志）
RUN pip install "git+https://github.com/facebookresearch/detectron2.git"

# 设置环境变量
ENV PATH /opt/conda/envs/pdf2ppt/bin:$PATH
ENV CONDA_DEFAULT_ENV pdf2ppt
ENV TESSERACT_CMD /usr/bin/tesseract
ENV POPPLER_PATH /usr/bin

# 复制应用代码
COPY . .

# 验证安装
RUN python -c "import detectron2; print(f'Detectron2 version: {detectron2.__version__}')"

CMD ["tail", "-f", "/dev/null"]