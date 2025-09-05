#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子选股系统主启动文件
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app

def main():
    """主函数"""
    # 获取环境配置
    config_name = os.getenv('FLASK_ENV', 'development')
    
    # 创建应用
    app = create_app(config_name)
    
    # 启动应用
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = config_name == 'development'
    
    print(f"启动多因子选股系统...")
    print(f"访问地址: http://{host}:{port}")
    print(f"管理界面: http://{host}:{port}/ml-factor")
    print("按 Ctrl+C 停止服务器")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()