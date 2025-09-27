# 使用官方 Python 3.12 slim 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /home

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 端口
EXPOSE 8600

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8600"]

