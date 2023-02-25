FROM python:3.7.9-alpine

LABEL maintainer="foo@bar.com"
ARG TZ='Asia/Shanghai'

ARG CHATGPT_ON_WECHAT_VER=1.0.2

ENV BUILD_PREFIX=/app \
    BUILD_OPEN_AI_API_KEY='YOUR OPEN AI KEY HERE'

RUN apk add --no-cache \
        bash \
        curl \
        wget \
        gcc \
        g++ \
        ca-certificates \
        openssh \ 
        libffi-dev 

RUN wget -t 3 -T 30 -nv -O chatgpt-on-wechat-${CHATGPT_ON_WECHAT_VER}.tar.gz \
          https://github.com/zhayujie/chatgpt-on-wechat/archive/refs/tags/${CHATGPT_ON_WECHAT_VER}.tar.gz \
    && tar -xzf chatgpt-on-wechat-${CHATGPT_ON_WECHAT_VER}.tar.gz \
    && mv chatgpt-on-wechat-${CHATGPT_ON_WECHAT_VER} ${BUILD_PREFIX} \
    && rm chatgpt-on-wechat-${CHATGPT_ON_WECHAT_VER}.tar.gz

WORKDIR ${BUILD_PREFIX}

RUN cd ${BUILD_PREFIX} \
    && cp config-template.json ${BUILD_PREFIX}/config.json \
    && sed -i "2s/YOUR API KEY/${BUILD_OPEN_AI_API_KEY}/" ${BUILD_PREFIX}/config.json

RUN /usr/local/bin/python -m pip install --no-cache --upgrade pip \
    && pip install --no-cache \
      itchat-uos==1.5.0.dev0  \
      openai \
      wechaty

ADD ./entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN adduser -D -h /home/noroot -u 1000 -s /bin/bash noroot \
    && chown noroot:noroot ${BUILD_PREFIX}

USER noroot

ENTRYPOINT ["/entrypoint.sh"]
