echo "# 获取当前日期时间"
current_datetime=$(date +"%Y%m%d_%H%M%S")

echo "# 检查并重命名 run.log，新运行用新建文件来放日志，防日志文件越来越大拖慢系统性能"
if [ -f "run.log" ]; then
    mv "run.log" "run.${current_datetime}_RenamedAsHistoryBak_YouCanDeleteMe.log"
fi

echo "# 检查并重命名 output.log，新运行用新建文件来放日志，防日志文件越来越大拖慢系统性能"
if [ -f "output.log" ]; then
    mv "output.log" "output.${current_datetime}_RenamedAsHistoryBak_YouCanDeleteMe.log"
fi

echo "看时间，设时区，再看时间"
date
sudo ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
sudo dpkg-reconfigure -f noninteractive tzdata
date

echo "启动 C-o-W 的 app.py，微信要扫的二维码用 _TAIL.sh 查看"
nohup python3 app.py > output.log 2>&1 &
disown
