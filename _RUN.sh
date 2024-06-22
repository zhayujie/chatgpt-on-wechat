date
sudo ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
sudo dpkg-reconfigure -f noninteractive tzdata
date

nohup python3 app.py > output.log 2>&1 &
sleep 2  # 等待2秒以确保文件被创建和开始写入
tail -f output.log
