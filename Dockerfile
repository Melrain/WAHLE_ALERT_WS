# 使用 Python 3.11 作为基础镜像（Railway 推荐使用较新的 Python 版本）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（如果需要）
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录（如果不存在）
RUN mkdir -p data/raw data/processed data/results

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 运行主程序（main_ws.py 是实时监控系统）
# 使用 -u 参数强制无缓冲输出，确保日志实时显示
CMD ["python", "-u", "main_ws.py"]

