"""
书签和笔记数据模型
"""
from backend.models.db import get_db_connection

def add_bookmark(book_id, page_number=None, position=None, note=None):
    """添加书签"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO bookmarks (book_id, page_number, position, note)
                VALUES (%s, %s, %s, %s)
            """, (book_id, page_number, position, note))
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def get_bookmarks_by_book(book_id):
    """获取指定图书的所有书签"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, book_id, page_number, position, note, created_at
                FROM bookmarks
                WHERE book_id = %s
                ORDER BY created_at DESC
            """, (book_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def update_bookmark(bookmark_id, page_number=None, position=None, note=None):
    """更新书签"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            updates = []
            params = []
            
            if page_number is not None:
                updates.append("page_number = %s")
                params.append(page_number)
            if position is not None:
                updates.append("position = %s")
                params.append(position)
            if note is not None:
                updates.append("note = %s")
                params.append(note)
            
            if updates:
                params.append(bookmark_id)
                cursor.execute(f"""
                    UPDATE bookmarks
                    SET {', '.join(updates)}
                    WHERE id = %s
                """, params)
                conn.commit()
                return True
            return False
    finally:
        conn.close()

def delete_bookmark(bookmark_id):
    """删除书签"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM bookmarks WHERE id = %s", (bookmark_id,))
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()

