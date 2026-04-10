# Flask 后端启动脚本
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置工作目录
os.chdir(project_root)

# 启动 Flask
from backend.app import create_app
app = create_app()
app.run(debug=False, host='0.0.0.0', port=5000)