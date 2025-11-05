"""
知乎采集器实现
使用组合模式，组合HTTP客户端和速率限制器
"""
from typing import List
from backend.collectors.interfaces import (
    CollectedQuestion, CollectedAnswer, CollectionConfig, QuestionCollector
)
from backend.collectors.collectors.base_collector import HTTPClient, RateLimiter
from datetime import datetime
import json
import os


class ZhihuCollector:
    """知乎问题采集器
    
    使用组合模式，组合HTTPClient和RateLimiter，而不是继承
    """
    
    def __init__(self):
        # 组合HTTP客户端
        self.http_client = HTTPClient(timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.zhihu.com/'
        })
        # 组合速率限制器（知乎API限制较严格，降低请求频率）
        self.rate_limiter = RateLimiter(requests_per_second=0.3)
        # 知乎搜索API（公开接口，无需认证）
        self.search_api = 'https://www.zhihu.com/api/v4/search_v3'
        self.question_api = 'https://www.zhihu.com/api/v4/questions'
        self.answer_api = 'https://www.zhihu.com/api/v4/questions/{question_id}/answers'
    
    def get_platform_name(self) -> str:
        """获取平台名称"""
        return "知乎"
    
    def is_available(self) -> bool:
        """检查是否可用"""
        # 知乎API是公开的，始终可用
        return True
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """采集知乎问题"""
        questions = []
        
        try:
            # 使用真实API采集
            questions = self._collect_from_api(config)
            print(f"[知乎采集器] 成功采集到 {len(questions)} 个问题")
        except Exception as e:
            import traceback
            print(f"[知乎采集器] 采集失败: {str(e)}")
            print(f"[知乎采集器] 错误详情: {traceback.format_exc()}")
            # API失败时返回空列表，不降级到模拟数据
            questions = []
        
        return questions
    
    def _collect_from_api(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """从真实API采集"""
        questions = []
        
        try:
            # 搜索问题
            self.rate_limiter.wait_if_needed()
            search_params = {
                'q': config.topic,
                't': 'general',
                'correction': 1,
                'offset': 0,
                'limit': min(config.max_results * 2, 50),  # 多获取一些，因为可能过滤
                'lc_idx': 0,
                'show_all_topics': 0
            }
            
            print(f"[知乎采集器] 搜索主题: {config.topic}")
            response = self.http_client.get(self.search_api, params=search_params)
            
            if response.status_code != 200:
                print(f"[知乎采集器] 搜索API返回状态码: {response.status_code}")
                return questions
            
            data = response.json()
            search_results = data.get('data', [])
            print(f"[知乎采集器] 搜索到 {len(search_results)} 个结果")
            
            # 提取问题
            question_ids = []
            for item in search_results:
                obj = item.get('object', {})
                obj_type = obj.get('type')
                
                # 查找问题
                if obj_type == 'question':
                    question_id = obj.get('id')
                    if question_id:
                        question_ids.append((question_id, obj))
                elif obj_type == 'answer':
                    # 如果是回答，获取关联的问题
                    question = obj.get('question', {})
                    question_id = question.get('id')
                    if question_id and question_id not in [qid for qid, _ in question_ids]:
                        question_ids.append((question_id, question))
            
            # 去重并限制数量
            seen_ids = set()
            unique_question_ids = []
            for qid, obj in question_ids:
                if qid not in seen_ids and len(unique_question_ids) < config.max_results:
                    seen_ids.add(qid)
                    unique_question_ids.append((qid, obj))
            
            print(f"[知乎采集器] 提取到 {len(unique_question_ids)} 个唯一问题")
            
            # 获取每个问题的详细信息
            for question_id, question_obj in unique_question_ids:
                try:
                    self.rate_limiter.wait_if_needed()
                    
                    # 获取问题详情
                    question_detail_url = f"{self.question_api}/{question_id}"
                    detail_response = self.http_client.get(question_detail_url)
                    
                    if detail_response.status_code == 200:
                        question_data = detail_response.json()
                        
                        # 采集回答（如果配置要求）
                        answers = []
                        if config.collect_answers:
                            answers = self._collect_answers(question_id, config)
                        
                        # 创建问题对象
                        created_time = question_data.get('created', 0)
                        if created_time:
                            try:
                                created_at = datetime.fromtimestamp(created_time)
                            except:
                                created_at = datetime.now()
                        else:
                            created_at = datetime.now()
                        
                        question = CollectedQuestion(
                            title=question_data.get('title', question_obj.get('title', '')),
                            content=question_data.get('detail', question_obj.get('excerpt', '')),
                            source=self.get_platform_name(),
                            source_url=f"https://www.zhihu.com/question/{question_id}",
                            author=None,  # 问题通常没有单一作者
                            created_at=created_at,
                            tags=[config.topic],
                            metadata={
                                'zhihu_id': question_id,
                                'answer_count': question_data.get('answer_count', 0),
                                'follower_count': question_data.get('follower_count', 0)
                            },
                            answers=answers
                        )
                        questions.append(question)
                        
                except Exception as e:
                    print(f"[知乎采集器] 获取问题 {question_id} 详情失败: {str(e)}")
                    # 如果获取详情失败，使用搜索结果中的基本信息
                    question = CollectedQuestion(
                        title=question_obj.get('title', ''),
                        content=question_obj.get('excerpt', ''),
                        source=self.get_platform_name(),
                        source_url=f"https://www.zhihu.com/question/{question_id}",
                        author=None,
                        created_at=datetime.now(),
                        tags=[config.topic],
                        metadata={'zhihu_id': question_id},
                        answers=[]
                    )
                    questions.append(question)
                    
        except Exception as e:
            import traceback
            print(f"[知乎采集器] API调用异常: {str(e)}")
            print(f"[知乎采集器] 异常详情: {traceback.format_exc()}")
        
        return questions
    
    def _collect_answers(self, question_id: str, config: CollectionConfig) -> List[CollectedAnswer]:
        """采集问题的回答"""
        answers = []
        
        try:
            self.rate_limiter.wait_if_needed()
            
            # 获取回答列表
            answer_url = self.answer_api.format(question_id=question_id)
            params = {
                'include': 'data[*].is_normal,admin_closed_comment,reward_info,content,comment_count,created_time,updated_time,excerpt,is_labeled,label_info,relationship.is_author,voting,is_thanked,is_nothelp,is_recognized;data[*].author.badge[*].topics',
                'limit': min(config.max_answers_per_question * 3, 20),  # 多获取一些用于筛选
                'offset': 0,
                'platform': 'desktop',
                'sort_by': 'default'
            }
            
            response = self.http_client.get(answer_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                answer_list = data.get('data', [])
                
                # 筛选高质量回答
                for answer_data in answer_list:
                    upvote_count = answer_data.get('voteup_count', 0)
                    
                    # 过滤低点赞数回答
                    if upvote_count < config.min_answer_upvotes:
                        continue
                    
                    # 提取回答内容
                    content = answer_data.get('content', '')
                    # 如果是HTML格式，提取纯文本
                    if content and '<' in content:
                        import re
                        # 简单去除HTML标签
                        content = re.sub(r'<[^>]+>', '', content)
                        content = content.replace('&nbsp;', ' ').strip()
                    
                    if not content:
                        continue
                    
                    # 获取作者信息
                    author = answer_data.get('author', {})
                    author_name = author.get('name', '匿名用户')
                    
                    # 创建回答对象
                    created_time = answer_data.get('created_time', 0)
                    if created_time:
                        try:
                            created_at = datetime.fromtimestamp(created_time)
                        except:
                            created_at = datetime.now()
                    else:
                        created_at = datetime.now()
                    
                    answer = CollectedAnswer(
                        content=content,
                        author=author_name,
                        upvotes=upvote_count,
                        downvotes=answer_data.get('votedown_count', 0),
                        source_url=f"https://www.zhihu.com/answer/{answer_data.get('id', '')}",
                        created_at=created_at,
                        metadata={
                            'zhihu_answer_id': answer_data.get('id'),
                            'comment_count': answer_data.get('comment_count', 0)
                        }
                    )
                    answers.append(answer)
                    
                    # 限制回答数量
                    if len(answers) >= config.max_answers_per_question:
                        break
                
                # 按点赞数排序
                answers.sort(key=lambda a: a.upvotes, reverse=True)
                
        except Exception as e:
            print(f"[知乎采集器] 采集问题 {question_id} 的回答失败: {str(e)}")
        
        return answers

