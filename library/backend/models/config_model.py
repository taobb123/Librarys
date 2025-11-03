"""
系统配置数据模型
"""
from backend.models.db import get_db_connection
import json

def get_config(key):
    """获取配置值"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT config_value FROM system_config WHERE config_key = %s
            """, (key,))
            result = cursor.fetchone()
            if result and result.get('config_value'):
                try:
                    return json.loads(result['config_value'])
                except:
                    return result['config_value']
            return None
    finally:
        conn.close()

def set_config(key, value):
    """设置配置值"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            value_json = json.dumps(value) if isinstance(value, (dict, list)) else value
            cursor.execute("""
                INSERT INTO system_config (config_key, config_value)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE config_value = VALUES(config_value), updated_at = NOW()
            """, (key, value_json))
            conn.commit()
            return True
    finally:
        conn.close()

def get_module_visibility():
    """获取模块显示配置"""
    config = get_config('module_visibility')
    if config is None:
        # 默认配置
        default = {'books': True, 'problems': True}
        set_config('module_visibility', default)
        return default
    return config

def set_module_visibility(books=None, problems=None):
    """设置模块显示配置"""
    current = get_module_visibility()
    if books is not None:
        current['books'] = books
    if problems is not None:
        current['problems'] = problems
    return set_config('module_visibility', current)

