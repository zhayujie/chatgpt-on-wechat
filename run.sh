#!/bin/bash
set -e

# ============================
# CowAgent Management Script
# ============================

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Emojis
EMOJI_ROCKET="🚀"
EMOJI_COW="🐄"
EMOJI_CHECK="✅"
EMOJI_CROSS="❌"
EMOJI_WARN="⚠️"
EMOJI_STOP="🛑"
EMOJI_WRENCH="🔧"

# Check if using Bash
if [ -z "$BASH_VERSION" ]; then
    echo -e "${RED}❌ Please run this script with Bash.${NC}"
    exit 1
fi

# Get current script directory
export BASE_DIR=$(cd "$(dirname "$0")"; pwd)

# Detect if in project directory
IS_PROJECT_DIR=false
if [ -f "${BASE_DIR}/config-template.json" ] && [ -f "${BASE_DIR}/app.py" ]; then
    IS_PROJECT_DIR=true
fi

# Check and install tool
check_and_install_tool() {
    local tool_name=$1
    if ! command -v "$tool_name" &> /dev/null; then
        echo -e "${YELLOW}⚙️  $tool_name not found, installing...${NC}"
        if command -v yum &> /dev/null; then
            sudo yum install "$tool_name" -y
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install "$tool_name" -y
        elif command -v brew &> /dev/null; then
            brew install "$tool_name"
        else
            echo -e "${RED}❌ Unsupported package manager. Please install $tool_name manually.${NC}"
            return 1
        fi

        if ! command -v "$tool_name" &> /dev/null; then
            echo -e "${RED}❌ Failed to install $tool_name.${NC}"
            return 1
        else
            echo -e "${GREEN}✅ $tool_name installed successfully.${NC}"
            return 0
        fi
    else
        echo -e "${GREEN}✅ $tool_name is already installed.${NC}"
        return 0
    fi
}

# Detect and set Python command
detect_python_command() {
    FOUND_NEWER_VERSION=""
    
    # Try to find Python command in order of preference
    for cmd in python3 python python3.12 python3.11 python3.10 python3.9 python3.8 python3.7; do
        if command -v $cmd &> /dev/null; then
            # Check Python version
            major_version=$($cmd -c 'import sys; print(sys.version_info[0])' 2>/dev/null)
            minor_version=$($cmd -c 'import sys; print(sys.version_info[1])' 2>/dev/null)
            
            if [[ "$major_version" == "3" ]]; then
                # Check if version is in supported range (3.7 - 3.12)
                if (( minor_version >= 7 && minor_version <= 12 )); then
                    PYTHON_CMD=$cmd
                    PYTHON_VERSION="${major_version}.${minor_version}"
                    break
                elif (( minor_version >= 13 )); then
                    # Found Python 3.13+, but not compatible
                    if [ -z "$FOUND_NEWER_VERSION" ]; then
                        FOUND_NEWER_VERSION="${major_version}.${minor_version}"
                    fi
                fi
            fi
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        echo -e "${YELLOW}Tried: python3, python, python3.12, python3.11, python3.10, python3.9, python3.8, python3.7${NC}"
        if [ -n "$FOUND_NEWER_VERSION" ]; then
            echo -e "${RED}❌ Found Python $FOUND_NEWER_VERSION, but this project requires Python 3.7-3.12${NC}"
            echo -e "${YELLOW}Python 3.13+ has compatibility issues with some dependencies (web.py, cgi module removed)${NC}"
            echo -e "${YELLOW}Please install Python 3.7-3.12 (recommend Python 3.12)${NC}"
        else
            echo -e "${RED}❌ No suitable Python found. Please install Python 3.7-3.12${NC}"
        fi
        exit 1
    fi
    
    # Export for global use
    export PYTHON_CMD
    export PYTHON_VERSION
    
    echo -e "${GREEN}✅ Found Python: $PYTHON_CMD (version $PYTHON_VERSION)${NC}"
}

# Check Python version (>= 3.7)
check_python_version() {
    detect_python_command
    
    # Verify pip is available
    if ! $PYTHON_CMD -m pip --version &> /dev/null; then
        echo -e "${RED}❌ pip not found for $PYTHON_CMD. Please install pip.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ pip is available for $PYTHON_CMD${NC}"
}

# Clone project
clone_project() {
    echo -e "${GREEN}🔍 Cloning ChatGPT-on-WeChat project...${NC}"

    if [ -d "chatgpt-on-wechat" ]; then
        echo -e "${YELLOW}⚠️  Directory 'chatgpt-on-wechat' already exists.${NC}"
        read -p "Choose action: overwrite(o), backup(b), or quit(q)? [press Enter for default: b]: " choice
        choice=${choice:-b}
        case "$choice" in
            o|O)
                echo -e "${YELLOW}🗑️  Overwriting 'chatgpt-on-wechat' directory...${NC}"
                rm -rf chatgpt-on-wechat
                ;;
            b|B)
                backup_dir="chatgpt-on-wechat_backup_$(date +%s)"
                echo -e "${YELLOW}🔀 Backing up to '$backup_dir'...${NC}"
                mv chatgpt-on-wechat "$backup_dir"
                ;;
            q|Q)
                echo -e "${RED}❌ Installation cancelled.${NC}"
                exit 1
                ;;
            *)
                echo -e "${RED}❌ Invalid choice. Exiting.${NC}"
                exit 1
                ;;
        esac
    fi

    check_and_install_tool git

    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}⚠️  Git not available. Trying wget/curl...${NC}"
        if command -v wget &> /dev/null; then
            wget https://gitee.com/zhayujie/chatgpt-on-wechat/repository/archive/master.zip -O chatgpt-on-wechat.zip
            unzip chatgpt-on-wechat.zip
            mv chatgpt-on-wechat-master chatgpt-on-wechat
            rm chatgpt-on-wechat.zip
        elif command -v curl &> /dev/null; then
            curl -L https://gitee.com/zhayujie/chatgpt-on-wechat/repository/archive/master.zip -o chatgpt-on-wechat.zip
            unzip chatgpt-on-wechat.zip
            mv chatgpt-on-wechat-master chatgpt-on-wechat
            rm chatgpt-on-wechat.zip
        else
            echo -e "${RED}❌ Cannot download project. Please install Git, wget, or curl.${NC}"
            exit 1
        fi
    else
        git clone https://github.com/zhayujie/chatgpt-on-wechat.git || \
        git clone https://gitee.com/zhayujie/chatgpt-on-wechat.git
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}❌ Project clone failed. Please check network connection.${NC}"
            exit 1
        fi
    fi

    cd chatgpt-on-wechat || { echo -e "${RED}❌ Failed to enter project directory.${NC}"; exit 1; }
    export BASE_DIR=$(pwd)
    echo -e "${GREEN}✅ Project cloned successfully: $BASE_DIR${NC}"
    
    # Add execute permission to management script
    if [ -f "${BASE_DIR}/run.sh" ]; then
        chmod +x "${BASE_DIR}/run.sh" 2>/dev/null || true
        echo -e "${GREEN}✅ Execute permission added to run.sh${NC}"
    fi
    
    sleep 1
}

# Install dependencies
install_dependencies() {
    echo -e "${GREEN}📦 Installing dependencies...${NC}"
    
    # For Python 3.11+, use --break-system-packages to avoid externally-managed-environment errors
    PIP_EXTRA_ARGS=""
    if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        PIP_EXTRA_ARGS="--break-system-packages"
        echo -e "${YELLOW}Python 3.11+ detected, using --break-system-packages for pip installations${NC}"
    fi
    
    # Upgrade pip and basic tools (ignore existing system packages to avoid conflicts)
    echo -e "${YELLOW}Upgrading pip and basic tools...${NC}"
    set +e
    $PYTHON_CMD -m pip install --upgrade pip setuptools wheel importlib_metadata --ignore-installed $PIP_EXTRA_ARGS -i https://pypi.tuna.tsinghua.edu.cn/simple > /tmp/pip_upgrade.log 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Some tools failed to upgrade, but continuing...${NC}"
        cat /tmp/pip_upgrade.log | head -20
    fi
    set -e
    rm -f /tmp/pip_upgrade.log
    
    # Common packages that may have distutils/system conflicts
    COMMON_CONFLICT_PACKAGES="PyYAML setuptools wheel certifi charset-normalizer"
    
    # Try normal installation first
    echo -e "${YELLOW}Installing project dependencies...${NC}"
    
    # Save output and capture exit code correctly
    set +e  # Temporarily disable exit on error
    $PYTHON_CMD -m pip install -r requirements.txt $PIP_EXTRA_ARGS -i https://pypi.tuna.tsinghua.edu.cn/simple > /tmp/pip_install.log 2>&1
    INSTALL_EXIT_CODE=$?
    set -e  # Re-enable exit on error
    
    # Show output
    cat /tmp/pip_install.log
    
    if [ $INSTALL_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Dependencies installed successfully.${NC}"
    else
        # Check if it's a distutils/system package conflict error
        if grep -qE "distutils installed project|uninstall-no-record-file|installed by debian" /tmp/pip_install.log; then
            echo -e "${YELLOW}⚠️  Detected system package conflict, retrying with workaround...${NC}"
            # Only ignore common conflict packages
            IGNORE_PACKAGES=""
            for pkg in $COMMON_CONFLICT_PACKAGES; do
                IGNORE_PACKAGES="$IGNORE_PACKAGES --ignore-installed $pkg"
            done
            
            if $PYTHON_CMD -m pip install -r requirements.txt $IGNORE_PACKAGES $PIP_EXTRA_ARGS -i https://pypi.tuna.tsinghua.edu.cn/simple; then
                echo -e "${GREEN}✅ Dependencies installed successfully (workaround applied).${NC}"
            else
                echo -e "${YELLOW}⚠️  Some dependencies may have issues, but continuing...${NC}"
            fi
        elif grep -q "externally-managed-environment" /tmp/pip_install.log; then
            echo -e "${YELLOW}⚠️  Detected externally-managed environment, retrying with --break-system-packages...${NC}"
            if $PYTHON_CMD -m pip install -r requirements.txt --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple; then
                echo -e "${GREEN}✅ Dependencies installed successfully (system packages override applied).${NC}"
            else
                echo -e "${YELLOW}⚠️  Some dependencies may have issues, but continuing...${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Installation had errors, but continuing...${NC}"
        fi
    fi
    
    rm -f /tmp/pip_install.log
}

# Select model
select_model() {
    echo ""
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo -e "${CYAN}${BOLD}   Select AI Model${NC}"
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo -e "${YELLOW}1) MiniMax (MiniMax-M2.1, MiniMax-M2.1-lightning, etc.)${NC}"
    echo -e "${YELLOW}2) Zhipu AI (glm-4.7, glm-4.6, etc.)${NC}"
    echo -e "${YELLOW}3) Qwen (qwen3-max, qwen-plus, qwq-plus, etc.)${NC}"
    echo -e "${YELLOW}4) Claude (claude-sonnet-4-5, claude-opus-4-0, etc.)${NC}"
    echo -e "${YELLOW}5) Gemini (gemini-3-flash-preview, gemini-2.5-pro, etc.)${NC}"
    echo -e "${YELLOW}6) OpenAI GPT (gpt-5.2, gpt-4.1, etc.)${NC}"
    echo -e "${YELLOW}7) LinkAI (access multiple models via one API)${NC}"
    echo ""
    
    while true; do
        read -p "Enter your choice [press Enter for default: 1 - MiniMax]: " model_choice
        model_choice=${model_choice:-1}
        case "$model_choice" in
            1|2|3|4|5|6|7)
                break
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1-7.${NC}"
                ;;
        esac
    done
}

# Configure model
configure_model() {
    case "$model_choice" in
        1)
            # MiniMax
            echo -e "${GREEN}Configuring MiniMax...${NC}"
            read -p "Enter MiniMax API Key: " minimax_key
            read -p "Enter model name [press Enter for default: MiniMax-M2.1]: " model_name
            model_name=${model_name:-MiniMax-M2.1}
            
            MODEL_NAME="$model_name"
            MINIMAX_KEY="$minimax_key"
            ;;
        2)
            # Zhipu AI
            echo -e "${GREEN}Configuring Zhipu AI...${NC}"
            read -p "Enter Zhipu AI API Key: " zhipu_key
            read -p "Enter model name [press Enter for default: glm-4.7]: " model_name
            model_name=${model_name:-glm-4.7}
            
            MODEL_NAME="$model_name"
            ZHIPU_KEY="$zhipu_key"
            ;;
        3)
            # Qwen (DashScope)
            echo -e "${GREEN}Configuring Qwen (DashScope)...${NC}"
            read -p "Enter DashScope API Key: " dashscope_key
            read -p "Enter model name [press Enter for default: qwen3-max]: " model_name
            model_name=${model_name:-qwen3-max}
            
            MODEL_NAME="$model_name"
            DASHSCOPE_KEY="$dashscope_key"
            ;;
        4)
            # Claude
            echo -e "${GREEN}Configuring Claude...${NC}"
            read -p "Enter Claude API Key: " claude_key
            read -p "Enter model name [press Enter for default: claude-sonnet-4-5]: " model_name
            model_name=${model_name:-claude-sonnet-4-5}
            read -p "Enter API Base URL [press Enter for default: https://api.anthropic.com/v1]: " api_base
            api_base=${api_base:-https://api.anthropic.com/v1}
            
            MODEL_NAME="$model_name"
            CLAUDE_KEY="$claude_key"
            CLAUDE_BASE="$api_base"
            ;;
        5)
            # Gemini
            echo -e "${GREEN}Configuring Gemini...${NC}"
            read -p "Enter Gemini API Key: " gemini_key
            read -p "Enter model name [press Enter for default: gemini-3-flash-preview]: " model_name
            model_name=${model_name:-gemini-3-flash-preview}
            read -p "Enter API Base URL [press Enter for default: https://generativelanguage.googleapis.com]: " api_base
            api_base=${api_base:-https://generativelanguage.googleapis.com}
            
            MODEL_NAME="$model_name"
            GEMINI_KEY="$gemini_key"
            GEMINI_BASE="$api_base"
            ;;
        6)
            # OpenAI
            echo -e "${GREEN}Configuring OpenAI GPT...${NC}"
            read -p "Enter OpenAI API Key: " openai_key
            read -p "Enter model name [press Enter for default: gpt-4.1]: " model_name
            model_name=${model_name:-gpt-4.1}
            read -p "Enter API Base URL [press Enter for default: https://api.openai.com/v1]: " api_base
            api_base=${api_base:-https://api.openai.com/v1}
            
            MODEL_NAME="$model_name"
            OPENAI_KEY="$openai_key"
            OPENAI_BASE="$api_base"
            ;;
        7)
            # LinkAI
            echo -e "${GREEN}Configuring LinkAI...${NC}"
            read -p "Enter LinkAI API Key: " linkai_key
            read -p "Enter model name [press Enter for default: MiniMax-M2.1]: " model_name
            model_name=${model_name:-MiniMax-M2.1}
            
            MODEL_NAME="$model_name"
            USE_LINKAI="true"
            LINKAI_KEY="$linkai_key"
            ;;
    esac
}

# Select channel
select_channel() {
    echo ""
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo -e "${CYAN}${BOLD}   Select Communication Channel${NC}"
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo -e "${YELLOW}1) Feishu (飞书)${NC}"
    echo -e "${YELLOW}2) DingTalk (钉钉)${NC}"
    echo -e "${YELLOW}3) WeCom (企微应用)${NC}"
    echo -e "${YELLOW}4) Web (网页)${NC}"
    echo ""
    
    while true; do
        read -p "Enter your choice [press Enter for default: 1 - Feishu]: " channel_choice
        channel_choice=${channel_choice:-1}
        case "$channel_choice" in
            1|2|3|4)
                break
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1-4.${NC}"
                ;;
        esac
    done
}

# Configure channel
configure_channel() {
    case "$channel_choice" in
        1)
            # Feishu (WebSocket mode)
            CHANNEL_TYPE="feishu"
            echo -e "${GREEN}Configure Feishu (WebSocket mode)...${NC}"
            read -p "Enter Feishu App ID: " fs_app_id
            read -p "Enter Feishu App Secret: " fs_app_secret
            read -p "Enter Feishu Bot Name: " fs_bot_name
            
            FEISHU_APP_ID="$fs_app_id"
            FEISHU_APP_SECRET="$fs_app_secret"
            FEISHU_BOT_NAME="$fs_bot_name"
            FEISHU_EVENT_MODE="websocket"
            ACCESS_INFO="Feishu channel configured (WebSocket mode)"
            ;;
        2)
            # DingTalk
            CHANNEL_TYPE="dingtalk"
            echo -e "${GREEN}Configure DingTalk...${NC}"
            read -p "Enter DingTalk Client ID: " dt_client_id
            read -p "Enter DingTalk Client Secret: " dt_client_secret
            
            DT_CLIENT_ID="$dt_client_id"
            DT_CLIENT_SECRET="$dt_client_secret"
            ACCESS_INFO="DingTalk channel configured"
            ;;
        3)
            # WeCom
            CHANNEL_TYPE="wechatcom_app"
            echo -e "${GREEN}Configure WeCom...${NC}"
            read -p "Enter WeChat Corp ID: " corp_id
            read -p "Enter WeChat Com App Token: " com_token
            read -p "Enter WeChat Com App Secret: " com_secret
            read -p "Enter WeChat Com App Agent ID: " com_agent_id
            read -p "Enter WeChat Com App AES Key: " com_aes_key
            read -p "Enter WeChat Com App Port [press Enter for default: 9898]: " com_port
            com_port=${com_port:-9898}
            
            WECHATCOM_CORP_ID="$corp_id"
            WECHATCOM_TOKEN="$com_token"
            WECHATCOM_SECRET="$com_secret"
            WECHATCOM_AGENT_ID="$com_agent_id"
            WECHATCOM_AES_KEY="$com_aes_key"
            WECHATCOM_PORT="$com_port"
            ACCESS_INFO="WeCom channel configured on port ${com_port}"
            ;;
        4)
            # Web
            CHANNEL_TYPE="web"
            read -p "Enter web port [press Enter for default: 9899]: " web_port
            web_port=${web_port:-9899}
            
            WEB_PORT="$web_port"
            ACCESS_INFO="Web interface will be available at: http://localhost:${web_port}/chat"
            ;;
    esac
}

# Generate config file
create_config_file() {
    echo -e "${GREEN}📝 Generating config.json...${NC}"
    
    # Build JSON based on channel type
    case "$CHANNEL_TYPE" in
        feishu)
            cat > config.json <<EOF
{
  "channel_type": "feishu",
  "model": "${MODEL_NAME}",
  "open_ai_api_key": "${OPENAI_KEY:-}",
  "open_ai_api_base": "${OPENAI_BASE:-https://api.openai.com/v1}",
  "claude_api_key": "${CLAUDE_KEY:-}",
  "claude_api_base": "${CLAUDE_BASE:-https://api.anthropic.com/v1}",
  "gemini_api_key": "${GEMINI_KEY:-}",
  "gemini_api_base": "${GEMINI_BASE:-https://generativelanguage.googleapis.com}",
  "zhipu_ai_api_key": "${ZHIPU_KEY:-}",
  "dashscope_api_key": "${DASHSCOPE_KEY:-}",
  "minimax_api_key": "${MINIMAX_KEY:-}",
  "voice_to_text": "openai",
  "text_to_voice": "openai",
  "voice_reply_voice": false,
  "speech_recognition": true,
  "group_speech_recognition": false,
  "use_linkai": ${USE_LINKAI:-false},
  "linkai_api_key": "${LINKAI_KEY:-}",
  "linkai_app_code": "",
  "feishu_bot_name": "${FEISHU_BOT_NAME}",
  "feishu_app_id": "${FEISHU_APP_ID}",
  "feishu_app_secret": "${FEISHU_APP_SECRET}",
  "dingtalk_client_id": "",
  "dingtalk_client_secret": "",
  "agent": true,
  "agent_max_context_tokens": 40000,
  "agent_max_context_turns": 30,
  "agent_max_steps": 15
}
EOF
            ;;
        web)
            cat > config.json <<EOF
{
  "channel_type": "web",
  "web_port": ${WEB_PORT},
  "model": "${MODEL_NAME}",
  "open_ai_api_key": "${OPENAI_KEY:-}",
  "open_ai_api_base": "${OPENAI_BASE:-https://api.openai.com/v1}",
  "claude_api_key": "${CLAUDE_KEY:-}",
  "claude_api_base": "${CLAUDE_BASE:-https://api.anthropic.com/v1}",
  "gemini_api_key": "${GEMINI_KEY:-}",
  "gemini_api_base": "${GEMINI_BASE:-https://generativelanguage.googleapis.com}",
  "zhipu_ai_api_key": "${ZHIPU_KEY:-}",
  "dashscope_api_key": "${DASHSCOPE_KEY:-}",
  "minimax_api_key": "${MINIMAX_KEY:-}",
  "voice_to_text": "openai",
  "text_to_voice": "openai",
  "voice_reply_voice": false,
  "speech_recognition": true,
  "group_speech_recognition": false,
  "use_linkai": ${USE_LINKAI:-false},
  "linkai_api_key": "${LINKAI_KEY:-}",
  "linkai_app_code": "",
  "feishu_bot_name": "$feishu_bot_name",
  "feishu_app_id": "",
  "feishu_app_secret": "",
  "dingtalk_client_id": "",
  "dingtalk_client_secret": "",
  "agent": true,
  "agent_max_context_tokens": 40000,
  "agent_max_context_turns": 30,
  "agent_max_steps": 15
}
EOF
            ;;
        dingtalk)
            cat > config.json <<EOF
{
  "channel_type": "dingtalk",
  "model": "${MODEL_NAME}",
  "open_ai_api_key": "${OPENAI_KEY:-}",
  "open_ai_api_base": "${OPENAI_BASE:-https://api.openai.com/v1}",
  "claude_api_key": "${CLAUDE_KEY:-}",
  "claude_api_base": "${CLAUDE_BASE:-https://api.anthropic.com/v1}",
  "gemini_api_key": "${GEMINI_KEY:-}",
  "gemini_api_base": "${GEMINI_BASE:-https://generativelanguage.googleapis.com}",
  "zhipu_ai_api_key": "${ZHIPU_KEY:-}",
  "dashscope_api_key": "${DASHSCOPE_KEY:-}",
  "minimax_api_key": "${MINIMAX_KEY:-}",
  "voice_to_text": "openai",
  "text_to_voice": "openai",
  "voice_reply_voice": false,
  "speech_recognition": true,
  "group_speech_recognition": false,
  "use_linkai": ${USE_LINKAI:-false},
  "linkai_api_key": "${LINKAI_KEY:-}",
  "linkai_app_code": "",
  "feishu_bot_name": "$feishu_bot_name",
  "feishu_app_id": "",
  "feishu_app_secret": "",
  "dingtalk_client_id": "${DT_CLIENT_ID}",
  "dingtalk_client_secret": "${DT_CLIENT_SECRET}",
  "agent": true,
  "agent_max_context_tokens": 40000,
  "agent_max_context_turns": 30,
  "agent_max_steps": 15
}
EOF
            ;;
        wechatcom_app)
            cat > config.json <<EOF
{
  "channel_type": "wechatcom_app",
  "wechatcom_corp_id": "${WECHATCOM_CORP_ID}",
  "wechatcomapp_token": "${WECHATCOM_TOKEN}",
  "wechatcomapp_secret": "${WECHATCOM_SECRET}",
  "wechatcomapp_agent_id": "${WECHATCOM_AGENT_ID}",
  "wechatcomapp_aes_key": "${WECHATCOM_AES_KEY}",
  "wechatcomapp_port": ${WECHATCOM_PORT},
  "model": "${MODEL_NAME}",
  "open_ai_api_key": "${OPENAI_KEY:-}",
  "open_ai_api_base": "${OPENAI_BASE:-https://api.openai.com/v1}",
  "claude_api_key": "${CLAUDE_KEY:-}",
  "claude_api_base": "${CLAUDE_BASE:-https://api.anthropic.com/v1}",
  "gemini_api_key": "${GEMINI_KEY:-}",
  "gemini_api_base": "${GEMINI_BASE:-https://generativelanguage.googleapis.com}",
  "zhipu_ai_api_key": "${ZHIPU_KEY:-}",
  "dashscope_api_key": "${DASHSCOPE_KEY:-}",
  "minimax_api_key": "${MINIMAX_KEY:-}",
  "voice_to_text": "openai",
  "text_to_voice": "openai",
  "voice_reply_voice": false,
  "speech_recognition": true,
  "group_speech_recognition": false,
  "use_linkai": ${USE_LINKAI:-false},
  "linkai_api_key": "${LINKAI_KEY:-}",
  "linkai_app_code": "",
  "feishu_bot_name": "$feishu_bot_name",
  "feishu_app_id": "",
  "feishu_app_secret": "",
  "dingtalk_client_id": "",
  "dingtalk_client_secret": "",
  "agent": true,
  "agent_max_context_tokens": 40000,
  "agent_max_context_turns": 30,
  "agent_max_steps": 15
}
EOF
            ;;
    esac

    echo -e "${GREEN}✅ Configuration file created successfully.${NC}"
}

# Start project
start_project() {
    echo ""
    echo -e "${GREEN}${EMOJI_ROCKET} Starting CowAgent...${NC}"
    sleep 1

    if [ ! -f "${BASE_DIR}/nohup.out" ]; then
        touch "${BASE_DIR}/nohup.out"
    fi

    OS_TYPE=$(uname)

    if [[ "$OS_TYPE" == "Linux" ]]; then
        # Linux: use setsid to detach from terminal
        nohup setsid $PYTHON_CMD "${BASE_DIR}/app.py" > "${BASE_DIR}/nohup.out" 2>&1 &
        echo -e "${GREEN}${EMOJI_COW} CowAgent started on Linux (using $PYTHON_CMD)${NC}"
    elif [[ "$OS_TYPE" == "Darwin" ]]; then
        # macOS: use nohup to prevent SIGHUP
        nohup $PYTHON_CMD "${BASE_DIR}/app.py" > "${BASE_DIR}/nohup.out" 2>&1 &
        echo -e "${GREEN}${EMOJI_COW} CowAgent started on macOS (using $PYTHON_CMD)${NC}"
    else
        echo -e "${RED}❌ Unsupported OS: ${OS_TYPE}${NC}"
        exit 1
    fi

    sleep 2
    echo ""
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo -e "${GREEN}${EMOJI_CHECK} CowAgent is now running in background!${NC}"
    echo -e "${GREEN}${EMOJI_CHECK} Process will continue after closing terminal.${NC}"
    echo -e "${CYAN}$ACCESS_INFO${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}Management Commands:${NC}"
    echo -e "  ${GREEN}./run.sh stop${NC}       Stop the service"
    echo -e "  ${GREEN}./run.sh restart${NC}    Restart the service"
    echo -e "  ${GREEN}./run.sh status${NC}     Check status"
    echo -e "  ${GREEN}./run.sh logs${NC}       View logs"
    echo -e "  ${GREEN}./run.sh update${NC}     Update and restart"
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}Showing recent logs (Ctrl+C to exit, agent keeps running):${NC}"
    sleep 2
    tail -n 30 -f "${BASE_DIR}/nohup.out"
}

# Show usage
show_usage() {
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo -e "${CYAN}${BOLD}   ${EMOJI_COW} CowAgent Management Script${NC}"
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  ${GREEN}./run.sh${NC}               ${CYAN}# Install/Configure project${NC}"
    echo -e "  ${GREEN}./run.sh <command>${NC}     ${CYAN}# Execute management command${NC}"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  ${GREEN}start${NC}      Start the service"
    echo -e "  ${GREEN}stop${NC}       Stop the service"
    echo -e "  ${GREEN}restart${NC}    Restart the service"
    echo -e "  ${GREEN}status${NC}     Check service status"
    echo -e "  ${GREEN}logs${NC}       View logs (tail -f)"
    echo -e "  ${GREEN}config${NC}     Reconfigure project"
    echo -e "  ${GREEN}update${NC}     Update and restart"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  ${GREEN}./run.sh start${NC}"
    echo -e "  ${GREEN}./run.sh logs${NC}"
    echo -e "  ${GREEN}./run.sh status${NC}"
    echo -e "${CYAN}${BOLD}=========================================${NC}"
}

# Check if service is running
is_running() {
    if [ -z "$PYTHON_CMD" ]; then
        detect_python_command 2>/dev/null || PYTHON_CMD="python3"
    fi
    pid=$(ps ax | grep -i app.py | grep "${BASE_DIR}" | grep "$PYTHON_CMD" | grep -v grep | awk '{print $1}')
    [ -n "$pid" ]
}

# Get service PID
get_pid() {
    if [ -z "$PYTHON_CMD" ]; then
        detect_python_command 2>/dev/null || PYTHON_CMD="python3"
    fi
    ps ax | grep -i app.py | grep "${BASE_DIR}" | grep "$PYTHON_CMD" | grep -v grep | awk '{print $1}'
}

# Start service
cmd_start() {
    # Check if config.json exists
    if [ ! -f "${BASE_DIR}/config.json" ]; then
        echo -e "${RED}${EMOJI_CROSS} config.json not found${NC}"
        echo -e "${YELLOW}Please run './run.sh' to configure first${NC}"
        exit 1
    fi
    
    if is_running; then
        echo -e "${YELLOW}${EMOJI_WARN} CowAgent is already running (PID: $(get_pid))${NC}"
        echo -e "${YELLOW}Use './run.sh restart' to restart${NC}"
        return
    fi
    
    check_python_version
    start_project
}

# Stop service
cmd_stop() {
    echo -e "${GREEN}${EMOJI_STOP} Stopping CowAgent...${NC}"
    
    if ! is_running; then
        echo -e "${YELLOW}${EMOJI_WARN} CowAgent is not running${NC}"
        return
    fi
    
    pid=$(get_pid)
    echo -e "${GREEN}Found running process (PID: ${pid})${NC}"
    
    kill ${pid}
    sleep 3
    
    if ps -p ${pid} > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Process not stopped, forcing termination...${NC}"
        kill -9 ${pid}
    fi
    
    echo -e "${GREEN}${EMOJI_CHECK} CowAgent stopped${NC}"
}

# Restart service
cmd_restart() {
    cmd_stop
    sleep 1
    cmd_start
}

# Check status
cmd_status() {
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo -e "${CYAN}${BOLD}   ${EMOJI_COW} CowAgent Status${NC}"
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    
    if is_running; then
        pid=$(get_pid)
        echo -e "${GREEN}Status:${NC} ✅ Running"
        echo -e "${GREEN}PID:${NC}    ${pid}"
        if [ -f "${BASE_DIR}/nohup.out" ]; then
            echo -e "${GREEN}Logs:${NC}   ${BASE_DIR}/nohup.out"
        fi
    else
        echo -e "${YELLOW}Status:${NC} ⭐ Stopped"
    fi
    
    if [ -f "${BASE_DIR}/config.json" ]; then
        model=$(grep -o '"model"[[:space:]]*:[[:space:]]*"[^"]*"' "${BASE_DIR}/config.json" | cut -d'"' -f4)
        channel=$(grep -o '"channel_type"[[:space:]]*:[[:space:]]*"[^"]*"' "${BASE_DIR}/config.json" | cut -d'"' -f4)
        echo -e "${GREEN}Model:${NC}  ${model}"
        echo -e "${GREEN}Channel:${NC} ${channel}"
    fi
    
    echo -e "${CYAN}${BOLD}=========================================${NC}"
}

# View logs
cmd_logs() {
    if [ -f "${BASE_DIR}/nohup.out" ]; then
        echo -e "${YELLOW}Viewing logs (Ctrl+C to exit):${NC}"
        tail -f "${BASE_DIR}/nohup.out"
    else
        echo -e "${RED}❌ Log file not found: ${BASE_DIR}/nohup.out${NC}"
    fi
}

# Reconfigure
cmd_config() {
    echo -e "${YELLOW}${EMOJI_WRENCH} Reconfiguring CowAgent...${NC}"
    
    if [ -f "${BASE_DIR}/config.json" ]; then
        backup_file="${BASE_DIR}/config.json.backup.$(date +%s)"
        cp "${BASE_DIR}/config.json" "${backup_file}"
        echo -e "${GREEN}✅ Backed up config to: ${backup_file}${NC}"
    fi
    
    check_python_version
    install_dependencies
    select_model
    configure_model
    select_channel
    configure_channel
    create_config_file
    
    echo ""
    read -p "Restart service now? [Y/n]: " restart_now
    if [[ ! $restart_now == [Nn]* ]]; then
        cmd_restart
    fi
}

# Update project
cmd_update() {
    echo -e "${GREEN}${EMOJI_WRENCH} Updating CowAgent...${NC}"
    cd "${BASE_DIR}"
    
    # Stop service
    if is_running; then
        cmd_stop
    fi
    
    # Update code
    if [ -d .git ]; then
        echo -e "${GREEN}🔄 Pulling latest code...${NC}"
        git pull || {
            echo -e "${YELLOW}⚠️  GitHub failed, trying Gitee...${NC}"
            git remote set-url origin https://gitee.com/zhayujie/chatgpt-on-wechat.git
            git pull
        }
    else
        echo -e "${YELLOW}⚠️  Not a git repository, skipping code update${NC}"
    fi
    
    # Reinstall dependencies
    check_python_version
    install_dependencies
    
    # Restart service
    cmd_start
}

# Installation mode
install_mode() {
    clear
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo -e "${CYAN}${BOLD}   ${EMOJI_COW} CowAgent Installation${NC}"
    echo -e "${CYAN}${BOLD}=========================================${NC}"
    echo ""
    sleep 1

    if [ "$IS_PROJECT_DIR" = true ]; then
        echo -e "${GREEN}✅ Detected existing project directory.${NC}"
        
        if [ -f "${BASE_DIR}/config.json" ]; then
            echo -e "${GREEN}✅ Project already configured${NC}"
            echo ""
            show_usage
            return
        fi
        
        echo -e "${YELLOW}📝 No config.json found. Let's configure your project!${NC}"
        echo ""
        
        # Project directory already exists, skip clone
        check_python_version
    else
        # Remote install mode, need to clone project
        check_python_version
        clone_project
    fi
    
    # Install dependencies and configure
    install_dependencies
    select_model
    configure_model
    select_channel
    configure_channel
    create_config_file
    
    echo ""
    read -p "Start CowAgent now? [Y/n]: " start_now
    if [[ ! $start_now == [Nn]* ]]; then
        start_project
    else
        echo -e "${GREEN}✅ Installation complete!${NC}"
        echo ""
        echo -e "${CYAN}${BOLD}To start manually:${NC}"
        echo -e "${YELLOW}  cd ${BASE_DIR}${NC}"
        echo -e "${YELLOW}  ./run.sh start${NC}"
        echo ""
        echo -e "${CYAN}Or use nohup directly:${NC}"
        echo -e "${YELLOW}  nohup $PYTHON_CMD app.py > nohup.out 2>&1 & tail -f nohup.out${NC}"
    fi
}

# Main function
main() {
    case "$1" in
        start)
            if [ "$IS_PROJECT_DIR" = false ]; then
                echo -e "${RED}❌ Must run in project directory${NC}"
                exit 1
            fi
            cmd_start
            ;;
        stop)
            if [ "$IS_PROJECT_DIR" = false ]; then
                echo -e "${RED}❌ Must run in project directory${NC}"
                exit 1
            fi
            cmd_stop
            ;;
        restart)
            if [ "$IS_PROJECT_DIR" = false ]; then
                echo -e "${RED}❌ Must run in project directory${NC}"
                exit 1
            fi
            cmd_restart
            ;;
        status)
            if [ "$IS_PROJECT_DIR" = false ]; then
                echo -e "${RED}❌ Must run in project directory${NC}"
                exit 1
            fi
            cmd_status
            ;;
        logs)
            if [ "$IS_PROJECT_DIR" = false ]; then
                echo -e "${RED}❌ Must run in project directory${NC}"
                exit 1
            fi
            cmd_logs
            ;;
        config)
            if [ "$IS_PROJECT_DIR" = false ]; then
                echo -e "${RED}❌ Must run in project directory${NC}"
                exit 1
            fi
            cmd_config
            ;;
        update)
            if [ "$IS_PROJECT_DIR" = false ]; then
                echo -e "${RED}❌ Must run in project directory${NC}"
                exit 1
            fi
            cmd_update
            ;;
        help|--help|-h)
            show_usage
            ;;
        "")
            # No command - install/configure mode
            install_mode
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
