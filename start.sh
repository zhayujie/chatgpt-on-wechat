ps -ef | grep app.py | grep -v grep | awk '{print $2}' | xargs kill
nohup /home/hfy/miniconda3/envs/gptac_venv/bin/python -u app.py >> wechat_robot.log 2>&1 &

