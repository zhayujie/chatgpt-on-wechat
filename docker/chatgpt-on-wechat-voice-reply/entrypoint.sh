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
SPEECH_RECOGNITION=${SPEECH_RECOGNITION:-""}
CHARACTER_DESC=${CHARACTER_DESC:-""}
EXPIRES_IN_SECONDS=${EXPIRES_IN_SECONDS:-""}

VOICE_REPLY_VOICE=${VOICE_REPLY_VOICE:-""}
BAIDU_APP_ID=${BAIDU_APP_ID:-""}
BAIDU_API_KEY=${BAIDU_API_KEY:-""}
BAIDU_SECRET_KEY=${BAIDU_SECRET_KEY:-""}

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
    sed -i "s/\"open_ai_api_key\".*,$/\"open_ai_api_key\": \"$OPEN_AI_API_KEY\",/" $CHATGPT_ON_WECHAT_CONFIG_PATH
else
    echo -e "\033[31m[Warning] You need to set OPEN_AI_API_KEY before running!\033[0m"
fi

# use http_proxy as default
if [ "$HTTP_PROXY" != "" ] ; then
    sed -i "s/\"proxy\".*,$/\"proxy\": \"$HTTP_PROXY\",/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$OPEN_AI_PROXY" != "" ] ; then
    sed -i "s/\"proxy\".*,$/\"proxy\": \"$OPEN_AI_PROXY\",/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$SINGLE_CHAT_PREFIX" != "" ] ; then
    sed -i "s/\"single_chat_prefix\".*,$/\"single_chat_prefix\": $SINGLE_CHAT_PREFIX,/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$SINGLE_CHAT_REPLY_PREFIX" != "" ] ; then
    sed -i "s/\"single_chat_reply_prefix\".*,$/\"single_chat_reply_prefix\": $SINGLE_CHAT_REPLY_PREFIX,/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$GROUP_CHAT_PREFIX" != "" ] ; then
    sed -i "s/\"group_chat_prefix\".*,$/\"group_chat_prefix\": $GROUP_CHAT_PREFIX,/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$GROUP_NAME_WHITE_LIST" != "" ] ; then
    sed -i "s/\"group_name_white_list\".*,$/\"group_name_white_list\": $GROUP_NAME_WHITE_LIST,/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$IMAGE_CREATE_PREFIX" != "" ] ; then
    sed -i "s/\"image_create_prefix\".*,$/\"image_create_prefix\": $IMAGE_CREATE_PREFIX,/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$CONVERSATION_MAX_TOKENS" != "" ] ; then
    sed -i "s/\"conversation_max_tokens\".*,$/\"conversation_max_tokens\": $CONVERSATION_MAX_TOKENS,/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$SPEECH_RECOGNITION" != "" ] ; then
    sed -i "s/\"speech_recognition\".*,$/\"speech_recognition\": $SPEECH_RECOGNITION,/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$CHARACTER_DESC" != "" ] ; then
    sed -i "s/\"character_desc\".*,$/\"character_desc\": \"$CHARACTER_DESC\",/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$EXPIRES_IN_SECONDS" != "" ] ; then
    sed -i "s/\"expires_in_seconds\".*$/\"expires_in_seconds\": $EXPIRES_IN_SECONDS/" $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

# append
if [ "$BAIDU_SECRET_KEY" != "" ] ; then
    sed -i "1a \ \ \"baidu_secret_key\": \"$BAIDU_SECRET_KEY\"," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$BAIDU_API_KEY" != "" ] ; then
    sed -i "1a \ \ \"baidu_api_key\": \"$BAIDU_API_KEY\"," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$BAIDU_APP_ID" != "" ] ; then
    sed -i "1a \ \ \"baidu_app_id\": \"$BAIDU_APP_ID\"," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

if [ "$VOICE_REPLY_VOICE" != "" ] ; then
    sed -i "1a \ \ \"voice_reply_voice\": $VOICE_REPLY_VOICE," $CHATGPT_ON_WECHAT_CONFIG_PATH
fi

# go to prefix dir
cd $CHATGPT_ON_WECHAT_PREFIX
# excute
$CHATGPT_ON_WECHAT_EXEC


