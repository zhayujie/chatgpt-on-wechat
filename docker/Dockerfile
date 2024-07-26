FROM python:3.10-slim-bullseye

# 设置维护人员信息
LABEL maintainer="Golu goluli@qq.com"

# 设置环境变量 无需shell交互
ENV DEBIAN_FRONTEND=noninteractive

# 更新系统包
RUN apt-get update -y

# 设置时区
ENV TZ=Asia/Shanghai
RUN echo "${TZ}" > /etc/timezone \
    && ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && apt update \
    && apt install -y tzdata \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
RUN apt-get update && apt-get install -y \
    sudo \
    supervisor \
    libnss3 \
    libnotify4 \
    libsecret-1-0 \
    libgbm1 \
    xvfb \
    zip \
    jq \
    libasound2 \
    fonts-wqy-zenhei \
    gnutls-bin \
    libglib2.0-dev \
    libdbus-1-3 \
    libgtk-3-0 \
    libxss1 \
    libxtst6 \
    libatspi2.0-0 \
    libx11-xcb1 \
    ffmpeg \
    unzip \
    dbus-user-session \
    curl && \
    apt autoremove -y && \
    apt clean && \
    rm -rf \
    /var/lib/apt/lists/* \
    /tmp/* \
    /var/tmp/*

# 设置工作目录
WORKDIR /app

# 复制当前目录下的所有文件到工作目录
COPY . .

#RUN chmod +x /app/napcat.sh
#RUN /app/napcat.sh
#RUN chmod +x /app/napcat_start.sh
#
#COPY . .

# 安装Linux QQ
RUN arch=$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/) && \
    curl -o linuxqq.deb https://dldir1.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.10_240715_${arch}_01.deb && \
    dpkg -i --force-depends linuxqq.deb && rm linuxqq.deb && \
    chmod +x napcat_start.sh && \
    echo "(async () => {await import('file:///app/napcat/napcat.mjs');})();" > /opt/QQ/resources/app/app_launcher/index.js
VOLUME /app/napcat/config
VOLUME /root/.config/QQ

# 获取 NapCatQQ 最新版本并下载
RUN arch=$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/) && \
    napcat_version=$(curl -s "https://api.github.com/repos/NapNeko/NapCatQQ/releases/latest" | jq -r '.tag_name') && \
    if [ "$napcat_version" = "" ]; then \
        echo "无法获取NapCatQQ版本，请检查错误。" && exit 1; \
    fi && \
    napcat_download_url="" && \
    if [ "$arch" = "amd64" ]; then \
        napcat_download_url="https://github.com/NapNeko/NapCatQQ/releases/download/$napcat_version/NapCat.linux.x64.zip"; \
    elif [ "$arch" = "arm64" ]; then \
        napcat_download_url="https://github.com/NapNeko/NapCatQQ/releases/download/$napcat_version/NapCat.linux.arm64.zip"; \
    else \
        echo "无法下载NapCatQQ，请检查错误。" && exit 1; \
    fi && \
    echo "NapCatQQ下载链接：$napcat_download_url" && \
    if [ "$arch" = "amd64" ]; then \
        download_arch="x64"; \
    else \
        download_arch="$arch"; \
    fi && \
    curl -L "$napcat_download_url" -o "NapCat.linux.$download_arch.zip" && \
    chmod +x napcat_start.sh

# 安装项目依赖
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-optional.txt

# 清理APT缓存
RUN apt-get clean

#ENTRYPOINT ["bash", "napcat_start.sh"]
# 运行 supervisord
ENTRYPOINT ["supervisord", "-c", "/app/docker/supervisord.conf"]
#CMD ["supervisord", "-c", "/app/supervisord.conf"]
#CMD ["python", "app.py"]

