#!/bin/bash

unset KUBECONFIG

cd .. && docker build -f docker/Dockerfile.latest \
             -t baojingyu/chatgpt-on-wechat .

docker tag baojingyu/chatgpt-on-wechat baojingyu/chatgpt-on-wechat:$(date +%Y%m%d)