sudo ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
sudo dpkg-reconfigure -f noninteractive tzdata

nohup python3 app.py > output.log 2>&1 &
tail -f output.log
