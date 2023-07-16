#!/bin/bash

unset KUBECONFIG

cd .. && docker build -f docker/Dockerfile.latest \
             -t zhayujie/chatgpt-on-wechat .

docker tag zhayujie/chatgpt-on-wechat JC0v0/chatgpt-on-wechat:$(date +%y%m%d)
