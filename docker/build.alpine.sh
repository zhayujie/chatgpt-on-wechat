#!/bin/bash

# fetch latest release tag
CHATGPT_ON_WECHAT_TAG=`curl -sL "https://api.github.com/repos/zhayujie/chatgpt-on-wechat/releases/latest" | \
     grep '"tag_name":' | \
     sed -E 's/.*"([^"]+)".*/\1/'`

# build image
docker build -f Dockerfile.alpine \
             --build-arg CHATGPT_ON_WECHAT_VER=$CHATGPT_ON_WECHAT_TAG \
             -t zhayujie/chatgpt-on-wechat .

# tag image
docker tag zhayujie/chatgpt-on-wechat zhayujie/chatgpt-on-wechat:alpine
docker tag zhayujie/chatgpt-on-wechat zhayujie/chatgpt-on-wechat:$CHATGPT_ON_WECHAT_TAG-alpine
