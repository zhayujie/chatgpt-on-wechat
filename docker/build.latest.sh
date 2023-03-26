#!/bin/bash

# move chatgpt-on-wechat
tar -zcf chatgpt-on-wechat.tar.gz --exclude=../../chatgpt-on-wechat/docker  ../../chatgpt-on-wechat

# build image
docker build -f Dockerfile.latest \
             -t zhayujie/chatgpt-on-wechat .