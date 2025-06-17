https://github.com/GobinFan/python-mcp-server-client/blob/main/README.md
# 创建项目目录
uv init guymcp
cd guymcp

# 创建并激活虚拟环境
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
uv add "mcp[cli]" httpx
# 创建并激活虚拟环境

退出虚deactivate

=============================文件说明
.env 大模型连接配置文件
server.py MCP服务端
client.py MCP客户端
requirements.txt 依赖包,通过pip3 install -r requirements.txt安装依赖
contacts.txt 联系人测试数据
tempbz.docx  考核表模板,用于测试
pyproject_template.toml 修改父目录pyproject.toml的模板
README.md 说明文件

=============================uv 安装，使用
pip3 install -r requirements.txt
修改父目录pyproject.toml,加入[project]项目,不然uv run 会报错
uv run server.py --host 127.0.0.1 --port 8020
测试server  curl -v http://127.0.0.1:8020/sse
uv run client.py http://127.0.0.1:8020/sse

==============================不用uv 安装依赖的另一种方法.建议使用uv
pip3 install -r requirements.txt
python server.py --host 127.0.0.1 --port 8020
python client.py http://127.0.0.1:8020/sse

==============================功能演示
按照安装说明，运行server.py，另开窗口运行client.py，输入提示词
1.为程康生成公务员年度考核表，替换'name,sex,birthday,injob,party,dwzw,csgz'的值为'程康，男,1971.4,1989.12，无,国家工商总局重庆市江津区市场监管局第三所，企业监管'
2.查询张三电话号码
3.查询所有姓李的电话

