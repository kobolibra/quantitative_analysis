import os
import sys

# 自动将当前目录添加到 Python 路径，确保能找到 app 模块
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, basedir)

from app import create_app

# 获取配置名，默认为 production
config_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name)

if __name__ == '__main__':
    # 使用环境变量中的端口，Render 必须要求绑定到 $PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
