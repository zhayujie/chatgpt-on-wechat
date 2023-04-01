#!/bin/bash

cd .. && docker build -f docker/Dockerfile.latest \
             -t zhayujie/chatgpt-on-wechat .