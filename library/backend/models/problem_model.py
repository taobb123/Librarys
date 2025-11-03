"""
问题数据模型
"""
from backend.models.db import get_db_connection
import json

def get_all_problems(category=None, tag=None):
    """获取所有问题列表
    
    Args:
        category: 分类筛选（可选）
        tag: 标签筛选（可选：兴趣、待办、已完成）
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            conditions = []
            params = []
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            
            if tag:
                conditions.append(f"JSON_CONTAINS(tags, JSON_QUOTE(%s), '$')")
                params.append(tag)
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT id, title, content, category, tags, related_book_ids, created_at, updated_at
                FROM problems
                {where_clause}
                ORDER BY created_at DESC
            """
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # 解析JSON字段
            for row in results:
                if row.get('tags'):
                    try:
                        row['tags'] = json.loads(row['tags']) if isinstance(row['tags'], str) else row['tags']
                    except:
                        row['tags'] = []
                else:
                    row['tags'] = []
                
                if row.get('related_book_ids'):
                    try:
                        ids = [int(x.strip()) for x in row['related_book_ids'].split(',') if x.strip()]
                        row['related_book_ids'] = ids
                    except:
                        row['related_book_ids'] = []
                else:
                    row['related_book_ids'] = []
            
            return results
    finally:
        conn.close()

def get_problem_by_id(problem_id):
    """根据ID获取问题"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, category, tags, related_book_ids, created_at, updated_at
                FROM problems
                WHERE id = %s
            """, (problem_id,))
            result = cursor.fetchone()
            
            if result:
                # 解析JSON字段
                if result.get('tags'):
                    try:
                        result['tags'] = json.loads(result['tags']) if isinstance(result['tags'], str) else result['tags']
                    except:
                        result['tags'] = []
                else:
                    result['tags'] = []
                
                if result.get('related_book_ids'):
                    try:
                        ids = [int(x.strip()) for x in result['related_book_ids'].split(',') if x.strip()]
                        result['related_book_ids'] = ids
                    except:
                        result['related_book_ids'] = []
                else:
                    result['related_book_ids'] = []
            
            return result
    finally:
        conn.close()

def add_problem(title, content, category=None, tags=None, related_book_ids=None):
    """添加问题"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 处理tags（JSON格式）
            tags_json = json.dumps(tags if tags else [])
            
            # 处理关联图书ID（逗号分隔字符串）
            book_ids_str = ','.join(str(id) for id in related_book_ids) if related_book_ids else None
            
            cursor.execute("""
                INSERT INTO problems (title, content, category, tags, related_book_ids)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, content, category, tags_json, book_ids_str))
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def update_problem(problem_id, title=None, content=None, category=None, tags=None, related_book_ids=None):
    """更新问题"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            
            if content is not None:
                updates.append("content = %s")
                params.append(content)
            
            if category is not None:
                updates.append("category = %s")
                params.append(category)
            
            if tags is not None:
                tags_json = json.dumps(tags)
                updates.append("tags = %s")
                params.append(tags_json)
            
            if related_book_ids is not None:
                book_ids_str = ','.join(str(id) for id in related_book_ids) if related_book_ids else None
                updates.append("related_book_ids = %s")
                params.append(book_ids_str)
            
            if not updates:
                return False
            
            updates.append("updated_at = NOW()")
            params.append(problem_id)
            
            cursor.execute(f"""
                UPDATE problems
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()

def delete_problem(problem_id):
    """删除问题"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM problems WHERE id = %s", (problem_id,))
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()

def update_problem_tags(problem_id, tags):
    """更新问题的标签"""
    return update_problem(problem_id, tags=tags)

