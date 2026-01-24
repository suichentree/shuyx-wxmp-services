# Dockerfile

# 使用与项目兼容的Python版本
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 39666

# 启动应用
# 使用多个worker提高性能
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "39666", "--workers", "4"]