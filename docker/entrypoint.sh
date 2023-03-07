#!/bin/bash
set -e

# build prefix
CHATGPT_ON_WECHAT_PREFIX=${CHATGPT_ON_WECHAT_PREFIX:-""}
# path to config.json
CHATGPT_ON_WECHAT_CONFIG_PATH=${CHATGPT_ON_WECHAT_CONFIG_PATH:-""}
# execution command line
CHATGPT_ON_WECHAT_EXEC=${CHATGPT_ON_WECHAT_EXEC:-""}

OPEN_AI_API_KEY=${OPEN_AI_API_KEY:-""}
OPEN_AI_PROXY=${OPEN_AI_PROXY:-""}
SINGLE_CHAT_PREFIX=${SINGLE_CHAT_PREFIX:-""}
SINGLE_CHAT_REPLY_PREFIX=${SINGLE_CHAT_REPLY_PREFIX:-""}
GROUP_CHAT_PREFIX=${GROUP_CHAT_PREFIX:-""}
GROUP_NAME_WHITE_LIST=${GROUP_NAME_WHITE_LIST:-""}
IMAGE_CREATE_PREFIX=${IMAGE_CREATE_PREFIX:-""}
CONVERSATION_MAX_TOKENS=${CONVERSATION_MAX_TOKENS:-""}
CHARACTER_DESC=${CHARACTER_DESC:-""}
EXPIRES_IN_SECONDS=${EXPIRES_IN_SECONDS:-""}

# CHATGPT_ON_WECHAT_PREFIX is empty, use /app
if [ "$CHATGPT_ON_WECHAT_PREFIX" == "" ] ; then
    CHATGPT_ON_WECHAT_PREFIX=/app
fi

# CHATGPT_ON_WECHAT_CONFIG_PATH is empty, use '/app/config.json'
if [ "$CHATGPT_ON_WECHAT_CONFIG_PATH" == "" ] ; then
    CHATGPT_ON_WECHAT_CONFIG_PATH=$CHATGPT_ON_WECHAT_PREFIX/config.json
fi

# CHATGPT_ON_WECHAT_EXEC is empty, use ‘python app.py’
if [ "$CHATGPT_ON_WECHAT_EXEC" == "" ] ; then
    CHATGPT_ON_WECHAT_EXEC="python app.py"
fi

# modify content in config.json
if [ "$OPEN_AI_API_KEY" != "" ] ; then
    sed -i "2c   \"open_ai_api_key\": \"$OPEN_AI_API_KEY\"," $CHATGPT_ON_WECHAT_CONFIG_PATH
else
    echo -e "\033[31m[Warning] You need to set OPEN_AI_API_KEY before running!\033[0m"
fi

# use http_proxy as default
if [ "$HTTP_PROXY" != "" ] ; then
    sed -i "3c   \"proxy\": \"$HTTP_PROXY\"," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$OPEN_AI_PROXY" != "" ] ; then
    sed -i "3c   \"proxy\": \"$OPEN_AI_PROXY\"," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$SINGLE_CHAT_PREFIX" != "" ] ; then
    sed -i "4c   \"single_chat_prefix\": $SINGLE_CHAT_PREFIX," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$SINGLE_CHAT_REPLY_PREFIX" != "" ] ; then
    sed -i "5c   \"single_chat_reply_prefix\": $SINGLE_CHAT_REPLY_PREFIX," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$GROUP_CHAT_PREFIX" != "" ] ; then
    sed -i "6c   \"group_chat_prefix\": $GROUP_CHAT_PREFIX," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$GROUP_NAME_WHITE_LIST" != "" ] ; then
    sed -i "7c   \"group_name_white_list\": $GROUP_NAME_WHITE_LIST," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$IMAGE_CREATE_PREFIX" != "" ] ; then
    sed -i "8c   \"image_create_prefix\": $IMAGE_CREATE_PREFIX," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$CONVERSATION_MAX_TOKENS" != "" ] ; then
    sed -i "9c   \"conversation_max_tokens\": $CONVERSATION_MAX_TOKENS," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$CHARACTER_DESC" != "" ] ; then
    sed -i "10c   \"character_desc\": \"$CHARACTER_DESC\"," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$EXPIRES_IN_SECONDS" != "" ] ; then
    sed -i "11c   \"expires_in_seconds\": $EXPIRES_IN_SECONDS" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

# go to prefix dir
cd $CHATGPT_ON_WECHAT_PREFIX
# excute
$CHATGPT_ON_WECHAT_EXEC


