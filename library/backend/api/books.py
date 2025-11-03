"""
图书相关API
"""
from flask import Blueprint, jsonify, request, send_file
from backend.models.book_model import get_all_books, get_books_by_category, get_book_by_id, scan_books_directory, delete_book
from backend.models.bookmark_model import add_bookmark, get_bookmarks_by_book, update_bookmark, delete_bookmark
from backend.config import Config
import os

# 尝试导入可选的依赖
try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False
    print("警告: BeautifulSoup4未安装，EPUB转换功能可能受限")

books_bp = Blueprint('books', __name__, url_prefix='/api/books')

@books_bp.route('/list', methods=['GET'])
def list_books():
    """获取图书列表"""
    category = request.args.get('category')
    if category:
        books = get_books_by_category(category)
    else:
        books = get_all_books()
    return jsonify({'success': True, 'data': books})

@books_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取分类列表"""
    from backend.models.book_model import get_categories
    categories = get_categories()
    return jsonify({'success': True, 'data': categories})

@books_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """获取图书详情"""
    book = get_book_by_id(book_id)
    if book:
        return jsonify({'success': True, 'data': book})
    return jsonify({'success': False, 'message': '图书不存在'}), 404

@books_bp.route('/<int:book_id>/file', methods=['GET'])
def get_book_file(book_id):
    """获取图书文件（用于在线阅读）"""
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({'success': False, 'message': '图书不存在'}), 404
    
    file_path = book['file_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': '文件不存在'}), 404
    
    # 根据文件类型返回不同的处理方式
    file_format = book.get('file_format', '').lower()
    
    # 定义MIME类型映射
    mimetypes = {
        'pdf': 'application/pdf',
        'epub': 'application/epub+zip',
        'txt': 'text/plain; charset=utf-8',
        'azw3': 'application/x-mobi8-ebook',
        'mobi': 'application/x-mobipocket-ebook',
        'html': 'text/html; charset=utf-8',
        'htm': 'text/html; charset=utf-8',
    }
    
    mimetype = mimetypes.get(file_format, 'application/octet-stream')
    return send_file(file_path, mimetype=mimetype)

@books_bp.route('/<int:book_id>/text', methods=['GET'])
def get_book_text(book_id):
    """获取图书文本内容（用于TXT、HTML等格式，以及EPUB等转换为文本）"""
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({'success': False, 'message': '图书不存在'}), 404
    
    file_path = book['file_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': '文件不存在'}), 404
    
    file_format = book.get('file_format', '').lower()
    
    try:
        # 处理纯文本格式（TXT、MD等）
        if file_format in ['txt', 'md', 'markdown']:
            content = read_text_file(file_path)
            return jsonify({
                'success': True,
                'content': content,
                'format': file_format,
                'type': 'text'
            })
        
        # 处理HTML格式
        elif file_format in ['html', 'htm']:
            content = read_text_file(file_path)
            return jsonify({
                'success': True,
                'content': content,
                'format': file_format,
                'type': 'html'
            })
        
        # 处理EPUB格式 - 转换为HTML
        elif file_format == 'epub':
            html_content = convert_epub_to_html(file_path)
            return jsonify({
                'success': True,
                'content': html_content,
                'format': 'html',
                'type': 'html',
                'original_format': 'epub'
            })
        
        else:
            return jsonify({'success': False, 'message': f'不支持将 {file_format.upper()} 格式转换为文本'}), 400
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"读取文件错误：{error_detail}")
        return jsonify({'success': False, 'message': f'读取文件失败: {str(e)}'}), 500


def read_text_file(file_path):
    """读取文本文件，自动检测编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                used_encoding = encoding
                break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        # 如果所有编码都失败，使用二进制模式读取
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            try:
                content = raw_data.decode('utf-8', errors='replace')
            except:
                content = raw_data.decode('latin-1', errors='replace')
    
    return content


def convert_epub_to_html(file_path):
    """将EPUB文件转换为HTML格式"""
    try:
        import ebooklib
        from ebooklib import epub
        
        # 读取EPUB文件
        book = epub.read_epub(file_path)
        
        # 提取所有章节内容
        html_parts = []
        
        # 添加基本样式
        html_parts.append("""
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
                line-height: 1.8;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }
            h1, h2, h3, h4, h5, h6 {
                margin-top: 24px;
                margin-bottom: 12px;
            }
            p {
                margin: 12px 0;
                text-align: justify;
            }
        </style>
        """)
        
        # 尝试使用BeautifulSoup解析（如果可用）
        if HAS_BEAUTIFULSOUP:
            try:
                from bs4 import BeautifulSoup
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        # 解析HTML内容
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        
                        # 移除脚本和样式标签
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # 提取文本内容
                        html_content = str(soup)
                        html_parts.append(html_content)
                
                if len(html_parts) > 1:  # 有实际内容
                    return '\n'.join(html_parts)
            except Exception:
                pass  # 如果BeautifulSoup失败，使用备用方案
        
        # 备用方案：简单的文本提取
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()
                try:
                    # 尝试直接解码
                    text = content.decode('utf-8')
                    # 简单的HTML清理
                    import re
                    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                    html_parts.append(f'<div>{text}</div>')
                except:
                    pass
        
        # 如果提取失败，返回基本信息
        if len(html_parts) == 1:  # 只有style
            return f"<div>无法解析EPUB文件内容。文件路径：{file_path}</div>"
        
        return '\n'.join(html_parts)
    
    except ImportError:
        raise Exception('ebooklib库未安装，无法转换EPUB文件')
    except Exception as e:
        raise Exception(f'EPUB转换失败: {str(e)}')

@books_bp.route('/scan', methods=['POST'])
def scan_books():
    """扫描图书目录并更新数据库"""
    try:
        # 检查是否启用更新模式
        update_mode = request.get_json().get('update', False) if request.is_json else False
        result = scan_books_directory(Config.BOOKS_PATH, update_existing=update_mode)
        
        # 确保返回的是字典格式
        if not isinstance(result, dict):
            result = {'added': 0, 'updated': 0, 'deleted': 0, 'total': 0, 'error': '扫描返回异常结果'}
        
        # 确保所有必需的字段存在
        result.setdefault('added', 0)
        result.setdefault('updated', 0)
        result.setdefault('deleted', 0)
        result.setdefault('total', result.get('added', 0) + result.get('updated', 0) + result.get('deleted', 0))
        
        message = f"扫描完成：新增 {result.get('added', 0)} 本"
        if result.get('updated', 0) > 0:
            message += f"，更新 {result.get('updated', 0)} 本"
        if result.get('deleted', 0) > 0:
            message += f"，删除 {result.get('deleted', 0)} 本"
        
        return jsonify({
            'success': True,
            'message': message,
            'data': result
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"扫描错误：{error_detail}")
        return jsonify({
            'success': False,
            'message': f'扫描失败：{str(e)}',
            'error': str(e)
        }), 500

@books_bp.route('/<int:book_id>/open-location', methods=['POST'])
def open_file_location(book_id):
    """在资源管理器中打开文件位置（Windows）"""
    import platform
    import subprocess
    
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({'success': False, 'message': '图书不存在'}), 404
    
    file_path = book['file_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': '文件不存在'}), 404
    
    try:
        system = platform.system()
        
        if system == 'Windows':
            # Windows: 使用explorer打开并选中文件
            subprocess.Popen(f'explorer /select,"{file_path}"', shell=True)
        elif system == 'Darwin':  # macOS
            # macOS: 使用open命令
            subprocess.Popen(['open', '-R', file_path])
        elif system == 'Linux':
            # Linux: 使用xdg-open打开文件管理器
            file_dir = os.path.dirname(file_path)
            subprocess.Popen(['xdg-open', file_dir])
        else:
            return jsonify({'success': False, 'message': f'不支持的操作系统: {system}'}), 400
        
        return jsonify({
            'success': True,
            'message': '已在资源管理器中打开文件位置'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'打开文件位置失败: {str(e)}'}), 500

@books_bp.route('/<int:book_id>/bookmarks', methods=['GET'])
def get_bookmarks(book_id):
    """获取图书的书签列表"""
    bookmarks = get_bookmarks_by_book(book_id)
    return jsonify({'success': True, 'data': bookmarks})

@books_bp.route('/<int:book_id>/bookmarks', methods=['POST'])
def create_bookmark(book_id):
    """创建书签"""
    data = request.get_json()
    bookmark_id = add_bookmark(
        book_id=book_id,
        page_number=data.get('page_number'),
        position=data.get('position'),
        note=data.get('note')
    )
    return jsonify({'success': True, 'data': {'id': bookmark_id}})

@books_bp.route('/bookmarks/<int:bookmark_id>', methods=['PUT'])
def update_bookmark_api(bookmark_id):
    """更新书签"""
    data = request.get_json()
    result = update_bookmark(
        bookmark_id=bookmark_id,
        page_number=data.get('page_number'),
        position=data.get('position'),
        note=data.get('note')
    )
    if result:
        return jsonify({'success': True, 'message': '更新成功'})
    return jsonify({'success': False, 'message': '更新失败'}), 400

@books_bp.route('/bookmarks/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark_api(bookmark_id):
    """删除书签"""
    result = delete_bookmark(bookmark_id)
    if result:
        return jsonify({'success': True, 'message': '删除成功'})
    return jsonify({'success': False, 'message': '删除失败'}), 404

@books_bp.route('/<int:book_id>', methods=['DELETE'])
def delete_book_api(book_id):
    """删除图书（从文件夹删除文件和数据库记录）"""
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({'success': False, 'message': '图书不存在'}), 404
    
    file_path = book['file_path']
    
    try:
        # 删除文件
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 删除数据库记录
        result = delete_book(book_id)
        if result:
            return jsonify({
                'success': True,
                'message': '图书已从文件夹删除'
            })
        else:
            return jsonify({'success': False, 'message': '删除数据库记录失败'}), 500
    
    except OSError as e:
        # 文件删除失败，但仍尝试删除数据库记录
        delete_book(book_id)
        return jsonify({
            'success': False,
            'message': f'删除文件失败: {str(e)}，但已从数据库中移除'
        }), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

