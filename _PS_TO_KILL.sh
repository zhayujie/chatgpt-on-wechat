echo "显示当前正在运行的 C-o-W 进程ID，然后用 kill 进程ID 杀掉"
ps -ef | grep app.py | grep -v grep
