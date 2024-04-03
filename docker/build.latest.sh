#!/bin/bash

unset KUBECONFIG

cd .. && docker build -f docker/Dockerfile.latest \
             -t hanfangyuan/dify-on-wechat .

docker tag hanfangyuan/dify-on-wechat hanfangyuan/dify-on-wechat:$(date +%y%m%d)
