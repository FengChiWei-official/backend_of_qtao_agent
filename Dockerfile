FROM continuumio/miniconda3


# 创建 app 用户和组
RUN groupadd -r app && useradd --no-log-init -r -g app app

# 设置工作目录
WORKDIR /app

# 复制环境配置并创建环境
COPY requirments.d/requirments.txt /app
RUN conda env create -n app 
# 激活环境
RUN conda run -n app pip install -r requirments.txt && conda clean -afy



# 激活环境（后续命令都在 base 环境下执行）
SHELL ["conda", "run", "-n", "app", "/bin/bash", "-c"]

# 复制项目代码（包含 config、src、static、dataset 等）
COPY src /app/src
COPY script /app/script
# 创建挂载点
RUN mkdir -p /app/static && chown app:app /app/static
RUN mkdir -p /app/dataset && chown app:app /app/dataset
# 经常变动的配置文件
RUN mkdir -p /app/config && chown app:app /app/config
# 还


# 暴露端口
EXPOSE 8000


# 切换到 app 用户
USER app

# 启动命令
CMD ["./app/start.sh"]