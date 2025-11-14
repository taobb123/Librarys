"""
回答数据模型
"""
from backend.models.db import get_db_connection
import json


def add_answer(problem_id, content, author=None, upvotes=0, downvotes=0, 
               quality_score=0.0, source_url=None):
    """添加回答"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO answers (problem_id, content, author, upvotes, downvotes, 
                                   quality_score, source_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (problem_id, content, author, upvotes, downvotes, 
                  quality_score, source_url))
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


def get_answers_by_problem_id(problem_id):
    """根据问题ID获取回答列表"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, problem_id, content, author, upvotes, downvotes,
                       quality_score, source_url, created_at, updated_at
                FROM answers
                WHERE problem_id = %s
                ORDER BY quality_score DESC, upvotes DESC
            """, (problem_id,))
            return cursor.fetchall()
    finally:
        conn.close()


def get_answer_by_id(answer_id):
    """根据ID获取回答"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, problem_id, content, author, upvotes, downvotes,
                       quality_score, source_url, created_at, updated_at
                FROM answers
                WHERE id = %s
            """, (answer_id,))
            return cursor.fetchone()
    finally:
        conn.close()


def update_answer(answer_id, content=None, upvotes=None, downvotes=None, 
                  quality_score=None):
    """更新回答"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            updates = []
            params = []
            
            if content is not None:
                updates.append("content = %s")
                params.append(content)
            
            if upvotes is not None:
                updates.append("upvotes = %s")
                params.append(upvotes)
            
            if downvotes is not None:
                updates.append("downvotes = %s")
                params.append(downvotes)
            
            if quality_score is not None:
                updates.append("quality_score = %s")
                params.append(quality_score)
            
            if not updates:
                return False
            
            updates.append("updated_at = NOW()")
            params.append(answer_id)
            
            cursor.execute(f"""
                UPDATE answers
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_answer(answer_id):
    """删除回答"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM answers WHERE id = %s", (answer_id,))
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()






