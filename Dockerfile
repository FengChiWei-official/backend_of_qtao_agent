FROM continuumio/miniconda3


# 创建 app 用户和组
RUN groupadd -r app && useradd --no-log-init -r -g app app

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并创建环境
COPY requirements.txt /app/requirements.txt
RUN conda create -n app python=3.10 -y 

# 激活环境（后续命令都在 app 环境下执行）
SHELL ["conda", "run", "-n", "app", "/bin/bash", "-c"]
RUN pip install -r /app/requirements.txt

# 复制项目代码（包含 config、src、static、dataset 等）
COPY src /app/src
# 创建挂载点
RUN mkdir -p /app/static /app/dataset /app/config /app/script /app/alembic /app/logs && \
    chown app:app /app/static /app/dataset /app/config /app/script /app/alembic /app/logs

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chown app:app /app/docker-entrypoint.sh

# 暴露端口
EXPOSE 8000

RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*
USER app


# 启动命令
CMD ["conda", "run", "--no-capture-output", "-n", "app", "bash", "/app/docker-entrypoint.sh"]