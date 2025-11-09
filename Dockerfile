# 使用官方 Python 镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装 uv (更快的包管理器)
RUN pip install --no-cache-dir uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY main.py config.py models.py ./
COPY routers ./routers/

# 使用 uv 安装依赖
RUN uv pip install --system --no-cache -r pyproject.toml

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
