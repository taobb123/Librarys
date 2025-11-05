"""
系统配置API
"""
from flask import Blueprint, jsonify, request
from backend.models.config_model import get_module_visibility, set_module_visibility

config_bp = Blueprint('config', __name__, url_prefix='/api/config')

@config_bp.route('/module-visibility', methods=['GET'])
def get_visibility():
    """获取模块显示配置"""
    visibility = get_module_visibility()
    return jsonify({'success': True, 'data': visibility})

@config_bp.route('/module-visibility', methods=['PUT'])
def update_visibility():
    """更新模块显示配置（只能选择一个模块）"""
    data = request.get_json()
    books = data.get('books', False)
    problems = data.get('problems', False)
    
    # 确保只能选择一个模块，如果两个都选或都不选，默认选择图书模块
    if books and problems:
        # 如果两个都选，只保留图书模块
        books = True
        problems = False
    elif not books and not problems:
        # 如果都不选，默认选择图书模块
        books = True
        problems = False
    
    set_module_visibility(books=books, problems=problems)
    visibility = get_module_visibility()
    return jsonify({'success': True, 'data': visibility})

