#!/usr/bin/env bash
set -e

# 颜色定义
RED='\033[0;31m'    # 红色
GREEN='\033[0;32m'  # 绿色
YELLOW='\033[0;33m' # 黄色
BLUE='\033[0;34m'   # 蓝色
NC='\033[0m'        # 无颜色

# 获取当前脚本的目录
export BASE_DIR=$(cd "$(dirname "$0")"; pwd)
echo -e "${GREEN}📁 BASE_DIR: ${BASE_DIR}${NC}"

# 检查 config.json 文件是否存在
check_config_file() {
    if [ ! -f "${BASE_DIR}/config.json" ]; then
        echo -e "${RED}❌ 错误：未找到 config.json 文件。请确保 config.json 存在于当前目录。${NC}"
        exit 1
    fi
}

# 检查 Python 版本是否大于等于 3.7，并检查 pip 是否可用
check_python_version() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ 错误：未找到 Python3。请安装 Python 3.7 或以上版本。${NC}"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

    if (( PYTHON_MAJOR < 3 || (PYTHON_MAJOR == 3 && PYTHON_MINOR < 7) )); then
        echo -e "${RED}❌ 错误：Python 版本为 ${PYTHON_VERSION}。请安装 Python 3.7 或以上版本。${NC}"
        exit 1
    fi

    if ! python3 -m pip --version &> /dev/null; then
        echo -e "${RED}❌ 错误：未找到 pip。请安装 pip。${NC}"
        exit 1
    fi
}

# 检查并安装缺失的依赖
install_dependencies() {
    echo -e "${YELLOW}⏳ 正在安装依赖...${NC}"

    if [ ! -f "${BASE_DIR}/requirements.txt" ]; then
        echo -e "${RED}❌ 错误：未找到 requirements.txt 文件。${NC}"
        exit 1
    fi

    # 安装 requirements.txt 中的依赖，使用清华大学的 PyPI 镜像
     pip3 install -r "${BASE_DIR}/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple

    # 处理 requirements-optional.txt（如果存在）
    if [ -f "${BASE_DIR}/requirements-optional.txt" ]; then
        echo -e "${YELLOW}⏳ 正在安装可选的依赖...${NC}"
        pip3 install -r "${BASE_DIR}/requirements-optional.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
    fi
}

# 启动项目
run_project() {
    echo -e "${GREEN}🚀 准备启动项目...${NC}"
    cd "${BASE_DIR}"
    sleep 2


    # 判断操作系统类型
    OS_TYPE=$(uname)

    if [[ "$OS_TYPE" == "Linux" ]]; then
        # 在 Linux 上使用 setsid
        setsid python3 "${BASE_DIR}/app.py" > "${BASE_DIR}/nohup.out" 2>&1 &
        echo -e "${GREEN}🚀 正在启动 ChatGPT-on-WeChat (Linux)...${NC}"
    elif [[ "$OS_TYPE" == "Darwin" ]]; then
        # 在 macOS 上直接运行
        python3 "${BASE_DIR}/app.py" > "${BASE_DIR}/nohup.out" 2>&1 &
        echo -e "${GREEN}🚀 正在启动 ChatGPT-on-WeChat (macOS)...${NC}"
    else
        echo -e "${RED}❌ 错误：不支持的操作系统 ${OS_TYPE}。${NC}"
        exit 1
    fi

    sleep 2
    # 显示日志输出，供用户扫码
    tail -n 30 -f "${BASE_DIR}/nohup.out"

}
# 更新项目
update_project() {
    echo -e "${GREEN}🔄 准备更新项目，现在停止项目...${NC}"
    cd "${BASE_DIR}"

    # 停止项目
    stop_project
    echo -e "${GREEN}🔄 开始更新项目...${NC}"
    # 更新代码，从 git 仓库拉取最新代码
    if [ -d .git ]; then
        GIT_PULL_OUTPUT=$(git pull)
        if [ $? -eq 0 ]; then
            if [[ "$GIT_PULL_OUTPUT" == *"Already up to date."* ]]; then
                echo -e "${GREEN}✅ 代码已经是最新的。${NC}"
            else
                echo -e "${GREEN}✅ 代码更新完成。${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️ 从 GitHub 更新失败，尝试切换到 Gitee 仓库...${NC}"
            # 更改远程仓库为 Gitee
            git remote set-url origin https://gitee.com/zhayujie/chatgpt-on-wechat.git
            GIT_PULL_OUTPUT=$(git pull)
            if [ $? -eq 0 ]; then
                if [[ "$GIT_PULL_OUTPUT" == *"Already up to date."* ]]; then
                    echo -e "${GREEN}✅ 代码已经是最新的。${NC}"
                else
                    echo -e "${GREEN}✅ 从 Gitee 更新成功。${NC}"
                fi
            else
                echo -e "${RED}❌ 错误：从 Gitee 更新仍然失败，请检查网络连接。${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${RED}❌ 错误：当前目录不是 git 仓库，无法更新代码。${NC}"
        exit 1
    fi

    # 安装依赖
    install_dependencies

    # 启动项目
    run_project
}

# 停止项目
stop_project() {
    echo -e "${GREEN}🛑 正在停止项目...${NC}"
    cd "${BASE_DIR}"
    pid=$(ps ax | grep -i app.py | grep "${BASE_DIR}" | grep python3 | grep -v grep | awk '{print $1}')
    if [ -z "$pid" ] ; then
        echo -e "${YELLOW}⚠️ 未找到正在运行的 ChatGPT-on-WeChat。${NC}"
        return
    fi

    echo -e "${GREEN}🛑 正在运行的 ChatGPT-on-WeChat (PID: ${pid})${NC}"

    kill ${pid}
    sleep 3

    if ps -p $pid > /dev/null; then
        echo -e "${YELLOW}⚠️ 进程未停止，尝试强制终止...${NC}"
        kill -9 ${pid}
    fi

    echo -e "${GREEN}✅ 已停止 ChatGPT-on-WeChat (PID: ${pid})${NC}"
}

# 主函数，根据用户参数执行操作
case "$1" in
    start)
        check_config_file
        check_python_version
        run_project
        ;;
    stop)
        stop_project
        ;;
    restart)
        stop_project
        check_config_file
        check_python_version
        run_project
        ;;
    update)
        check_config_file
        check_python_version
        update_project
        ;;
    *)
        echo -e "${YELLOW}=========================================${NC}"
        echo -e "${YELLOW}用法：${GREEN}$0 ${BLUE}{start|stop|restart|update}${NC}"
        echo -e "${YELLOW}示例：${NC}"
        echo -e "  ${GREEN}$0 ${BLUE}start${NC}"
        echo -e "  ${GREEN}$0 ${BLUE}stop${NC}"
        echo -e "  ${GREEN}$0 ${BLUE}restart${NC}"
        echo -e "  ${GREEN}$0 ${BLUE}update${NC}"
        echo -e "${YELLOW}=========================================${NC}"
        exit 1
        ;;
esac