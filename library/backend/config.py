"""
数据库配置文件
"""
import os

class Config:
    # MySQL数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'guox123123')
    MYSQL_DATABASE = 'library'
    
    # 图书文件路径
    BOOKS_PATH = os.getenv('BOOKS_PATH', 'D:\\Books')
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('FLASK_PORT', 5001))  # 服务器端口，默认5001
    
    # 第三方API配置
    # 聚合数据API密钥（用于微信热搜等）
    JUHE_API_KEY = 'd309075150e27978571dcb7d8c48bacc'
    USE_THIRD_PARTY_API = os.getenv('USE_THIRD_PARTY_API', 'false').lower() == 'true'

