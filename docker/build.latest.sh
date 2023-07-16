#!/bin/bash

unset KUBECONFIG

cd .. && docker build -f docker/Dockerfile.latest \
             -t JC0v0/chatgpt-on-wechat .

docker tag JC0v0/chatgpt-on-wechat JC0v0/chatgpt-on-wechat:$(date +%y%m%d)
