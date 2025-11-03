"""
图书数据模型
"""
from backend.models.db import get_db_connection
import os

def get_all_books():
    """获取所有图书列表"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, file_path, file_format, author, country, year, category, file_size
                FROM books
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()
    finally:
        conn.close()

def get_books_by_category(category):
    """根据分类获取图书"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, file_path, file_format, author, country, year, category, file_size
                FROM books
                WHERE category = %s
                ORDER BY created_at DESC
            """, (category,))
            return cursor.fetchall()
    finally:
        conn.close()

def get_book_by_id(book_id):
    """根据ID获取图书"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, file_path, file_format, author, country, year, category, file_size
                FROM books
                WHERE id = %s
            """, (book_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def add_book(title, file_path, file_format=None, author=None, country=None, year=None, category=None, file_size=None):
    """添加图书"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO books (title, file_path, file_format, author, country, year, category, file_size)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, file_path, file_format, author, country, year, category, file_size))
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def get_categories():
    """获取所有分类"""
    categories = ['文学', '金融', '科技', '历史', '艺术']
    result = {}
    for category in categories:
        books = get_books_by_category(category)
        result[category] = len(books)
    return result

def delete_book(book_id):
    """删除图书（从数据库）"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()

def scan_books_directory(books_path, update_existing=False):
    """扫描图书目录，自动添加图书到数据库
    
    Args:
        books_path: 图书目录路径
        update_existing: 是否更新已存在的图书信息（文件大小等）
    """
    if not os.path.exists(books_path):
        error_msg = f"图书目录不存在：{books_path}"
        print(error_msg)
        return {
            'added': 0,
            'updated': 0,
            'deleted': 0,
            'total': 0,
            'error': error_msg
        }
    
    supported_formats = ['.pdf', '.epub', '.azw3', '.mobi', '.txt', '.md', '.markdown', '.html', '.htm']
    added_count = 0
    updated_count = 0
    
    # 获取数据库中所有现有的文件路径
    conn = get_db_connection()
    existing_books = {}
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, file_path, file_size FROM books")
            for row in cursor.fetchall():
                existing_books[row['file_path']] = {
                    'id': row['id'],
                    'file_size': row['file_size']
                }
    finally:
        conn.close()
    
    # 跟踪扫描到的文件
    scanned_files = set()
    
    # 扫描目录
    for root, dirs, files in os.walk(books_path):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in supported_formats:
                file_path = os.path.join(root, file)
                scanned_files.add(file_path)
                
                # 获取文件大小
                try:
                    file_size = os.path.getsize(file_path)
                except OSError:
                    print(f"无法访问文件：{file_path}")
                    continue
                
                # 从文件路径推断分类（如果路径中包含分类名称）
                category = None
                for cat in ['文学', '金融', '科技', '历史', '艺术']:
                    if cat in file_path:
                        category = cat
                        break
                
                # 检查是否已存在
                if file_path in existing_books:
                    existing_book = existing_books[file_path]
                    # 如果启用了更新，且文件大小发生变化，则更新
                    if update_existing and existing_book['file_size'] != file_size:
                        conn = get_db_connection()
                        try:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE books 
                                    SET file_size = %s, category = %s, updated_at = NOW()
                                    WHERE id = %s
                                """, (file_size, category, existing_book['id']))
                                conn.commit()
                                updated_count += 1
                                print(f"已更新图书：{os.path.basename(file_path)}")
                        finally:
                            conn.close()
                else:
                    # 添加新图书
                    title = os.path.splitext(file)[0]
                    add_book(
                        title=title,
                        file_path=file_path,
                        file_format=file_ext[1:],  # 去掉点号
                        category=category,
                        file_size=file_size
                    )
                    added_count += 1
                    print(f"已添加图书：{title}")
    
    # 删除数据库中不存在的文件
    deleted_count = 0
    files_to_delete = set(existing_books.keys()) - scanned_files
    if files_to_delete:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                for file_path in files_to_delete:
                    book_id = existing_books[file_path]['id']
                    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
                    deleted_count += 1
                    print(f"已删除不存在的图书：{os.path.basename(file_path)}")
            conn.commit()
        finally:
            conn.close()
    
    result = {
        'added': added_count,
        'updated': updated_count,
        'deleted': deleted_count,
        'total': added_count + updated_count + deleted_count
    }
    print(f"扫描完成：新增 {added_count} 本，更新 {updated_count} 本，删除 {deleted_count} 本")
    return result

