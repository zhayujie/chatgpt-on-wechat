#!/bin/bash
set -e

# build prefix
DIFY_ON_WECHAT_PREFIX=${DIFY_ON_WECHAT_PREFIX:-""}
# path to config.json
DIFY_ON_WECHAT_CONFIG_PATH=${DIFY_ON_WECHAT_CONFIG_PATH:-""}
# execution command line
DIFY_ON_WECHAT_EXEC=${DIFY_ON_WECHAT_EXEC:-""}

# use environment variables to pass parameters
# if you have not defined environment variables, set them below
# export OPEN_AI_API_KEY=${OPEN_AI_API_KEY:-'YOUR API KEY'}
# export OPEN_AI_PROXY=${OPEN_AI_PROXY:-""}
# export SINGLE_CHAT_PREFIX=${SINGLE_CHAT_PREFIX:-'["bot", "@bot"]'}
# export SINGLE_CHAT_REPLY_PREFIX=${SINGLE_CHAT_REPLY_PREFIX:-'"[bot] "'}
# export GROUP_CHAT_PREFIX=${GROUP_CHAT_PREFIX:-'["@bot"]'}
# export GROUP_NAME_WHITE_LIST=${GROUP_NAME_WHITE_LIST:-'["ChatGPT测试群", "ChatGPT测试群2"]'}
# export IMAGE_CREATE_PREFIX=${IMAGE_CREATE_PREFIX:-'["画", "看", "找"]'}
# export CONVERSATION_MAX_TOKENS=${CONVERSATION_MAX_TOKENS:-"1000"}
# export SPEECH_RECOGNITION=${SPEECH_RECOGNITION:-"False"}
# export CHARACTER_DESC=${CHARACTER_DESC:-"你是ChatGPT, 一个由OpenAI训练的大型语言模型, 你旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。"}
# export EXPIRES_IN_SECONDS=${EXPIRES_IN_SECONDS:-"3600"}

# DIFY_ON_WECHAT_PREFIX is empty, use /app
if [ "$DIFY_ON_WECHAT_PREFIX" == "" ] ; then
    DIFY_ON_WECHAT_PREFIX=/app
fi

# DIFY_ON_WECHAT_CONFIG_PATH is empty, use '/app/config.json'
if [ "$DIFY_ON_WECHAT_CONFIG_PATH" == "" ] ; then
    DIFY_ON_WECHAT_CONFIG_PATH=$DIFY_ON_WECHAT_PREFIX/config.json
fi

# DIFY_ON_WECHAT_EXEC is empty, use ‘python app.py’
if [ "$DIFY_ON_WECHAT_EXEC" == "" ] ; then
    DIFY_ON_WECHAT_EXEC="python app.py"
fi

# modify content in config.json
# if [ "$OPEN_AI_API_KEY" == "YOUR API KEY" ] || [ "$OPEN_AI_API_KEY" == "" ]; then
#     echo -e "\033[31m[Warning] You need to set OPEN_AI_API_KEY before running!\033[0m"
# fi


# go to prefix dir
cd $DIFY_ON_WECHAT_PREFIX
# excute
$DIFY_ON_WECHAT_EXEC
