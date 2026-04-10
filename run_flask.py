import sys
import os

# 设置工作目录
os.chdir(r'c:\Users\lenovo\Desktop\TestMasterProject')
sys.path.insert(0, r'c:\Users\lenovo\Desktop\TestMasterProject')

# 启动 Flask
from backend.app import create_app
app = create_app()
app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)