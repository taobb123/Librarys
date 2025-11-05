"""
数据库连接管理
"""
import pymysql
from backend.config import Config

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def init_database():
    """初始化数据库和表结构"""
    # 先连接到MySQL服务器（不指定数据库）
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with conn.cursor() as cursor:
            # 创建数据库（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            
            # 切换到目标数据库
            cursor.execute(f"USE {Config.MYSQL_DATABASE}")
            
            # 创建分类表（公用数据表）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    文学 VARCHAR(100),
                    金融 VARCHAR(100),
                    科技 VARCHAR(100),
                    历史 VARCHAR(100),
                    艺术 VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建图书表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL COMMENT '书名',
                    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
                    file_format VARCHAR(10) COMMENT '文件格式(pdf/epub/azw3/mobi)',
                    author VARCHAR(100) COMMENT '作者',
                    country VARCHAR(50) COMMENT '国家',
                    year INT COMMENT '年代',
                    category VARCHAR(50) COMMENT '分类(文学/金融/科技/历史/艺术)',
                    file_size BIGINT COMMENT '文件大小(字节)',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_author (author)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建问题表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS problems (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL COMMENT '问题标题',
                    content TEXT NOT NULL COMMENT '问题内容',
                    category VARCHAR(50) COMMENT '问题分类(文学/金融/科技/历史/艺术)',
                    tags JSON COMMENT '标签JSON数组，包含：兴趣、待办、已完成',
                    related_book_ids VARCHAR(500) COMMENT '关联的图书ID列表,逗号分隔',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建回答表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    problem_id INT NOT NULL COMMENT '问题ID',
                    content TEXT NOT NULL COMMENT '回答内容',
                    author VARCHAR(100) COMMENT '回答作者',
                    upvotes INT DEFAULT 0 COMMENT '点赞数',
                    downvotes INT DEFAULT 0 COMMENT '点踩数',
                    quality_score DECIMAL(5,3) DEFAULT 0.000 COMMENT '质量评分(0-1)',
                    source_url VARCHAR(500) COMMENT '来源链接',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
                    INDEX idx_problem_id (problem_id),
                    INDEX idx_quality_score (quality_score),
                    INDEX idx_upvotes (upvotes)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建系统配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
                    config_value TEXT COMMENT '配置值(JSON格式)',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_config_key (config_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 初始化系统配置（显示图书和问题模块）
            cursor.execute("""
                INSERT INTO system_config (config_key, config_value)
                VALUES ('module_visibility', '{"books": true, "problems": true}')
                ON DUPLICATE KEY UPDATE config_value = VALUES(config_value)
            """)
            
            # 创建书签表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    book_id INT NOT NULL COMMENT '图书ID',
                    page_number INT COMMENT '页码或位置',
                    position VARCHAR(100) COMMENT '具体位置信息',
                    note TEXT COMMENT '笔记内容',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                    INDEX idx_book_id (book_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            conn.commit()
            print("数据库初始化成功！")
            
    except Exception as e:
        print(f"数据库初始化失败：{str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

