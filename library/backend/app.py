"""
Flask应用入口
"""
from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# 获取项目根目录并添加到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # 项目根目录
sys.path.insert(0, project_root)

# 现在可以导入backend模块
from backend.api.books import books_bp
from backend.api.problems import problems_bp
from backend.api.config import config_bp
from backend.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS，允许前端访问
CORS(app)

# 注册蓝图
app.register_blueprint(books_bp)
app.register_blueprint(problems_bp)
app.register_blueprint(config_bp)

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': 'Library API is running'})

@app.route('/')
def index():
    """根路径"""
    return jsonify({'message': 'Library API Server'})

if __name__ == '__main__':
    # 初始化数据库
    print("正在初始化数据库...")
    try:
        from backend.models.db import init_database
        init_database()
    except Exception as e:
        print(f"数据库初始化警告：{str(e)}")
        print("请确保MySQL服务已启动，并检查config.py中的数据库配置")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)

