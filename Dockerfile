# 使用 Python 3.9 作为基础镜像
FROM python:3.9

# 将工作目录设置为 /app
WORKDIR /app

# 复制当前目录下的所有文件（包括 requirements.txt 文件）
COPY . /app

# 安装所需的 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

RUN python manage.py migrate

# 对外暴露 8000 端口
EXPOSE 8000

# 运行 Django Web 应用
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]