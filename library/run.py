"""
项目启动脚本 - 从项目根目录运行
用法: python run.py
"""
import os
import sys

# 确保项目根目录在Python路径中
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入并运行Flask应用
if __name__ == '__main__':
    from backend.app import app
    
    # 初始化数据库
    print("正在初始化数据库...")
    try:
        from backend.models.db import init_database
        init_database()
    except Exception as e:
        print(f"数据库初始化警告：{str(e)}")
        print("请确保MySQL服务已启动，并检查backend/config.py中的数据库配置")
    
    # 启动Flask应用
    from backend.config import Config
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)

