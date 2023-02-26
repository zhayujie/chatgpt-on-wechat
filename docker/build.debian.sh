#!/bin/bash

CHATGPT_ON_WECHAT_TAG=1.0.2

docker build -f Dockerfile.debian \
             --build-arg CHATGPT_ON_WECHAT_VER=$CHATGPT_ON_WECHAT_TAG \
             -t zhayujie/chatgpt-on-wechat .

docker tag zhayujie/chatgpt-on-wechat zhayujie/chatgpt-on-wechat:$CHATGPT_ON_WECHAT_TAG-debian