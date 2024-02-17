ps -ef | grep app.py | grep -v grep | awk '{print $2}' | xargs kill

