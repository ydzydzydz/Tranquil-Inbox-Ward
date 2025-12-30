FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV OLLAMA_MODEL=mollysama/rwkv-7-g1b:1.5b \
    OLLAMA_API_URL=http://127.0.0.1:11434/api/generate \
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8501 \
    SERVER_TIMEOUT=60

# 暴露端口
EXPOSE 8501

# 设置默认命令
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
