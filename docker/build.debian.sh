docker build -f Dockerfile.debian \
             --build-arg CHATGPT_ON_WECHAT_VER=1.0.0\
             -t zhayujie/chatgpt-on-wechat:1.0.0-debian .