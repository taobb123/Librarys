"""
微博采集器实现
"""
from typing import List
from backend.collectors.interfaces import (
    CollectedQuestion, CollectedAnswer, CollectionConfig, QuestionCollector
)
from backend.collectors.collectors.base_collector import HTTPClient, RateLimiter
from datetime import datetime
import os


class WeiboCollector:
    """微博问题采集器"""
    
    def __init__(self):
        # 组合HTTP客户端
        self.http_client = HTTPClient(timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://weibo.com/'
        })
        # 组合速率限制器
        self.rate_limiter = RateLimiter(requests_per_second=0.2)
        
        # 微博开放平台API配置（OAuth 2.0）
        # 参考: https://open.weibo.com/wiki/微博API
        self.app_key = os.getenv('WEIBO_APP_KEY', '')
        self.app_secret = os.getenv('WEIBO_APP_SECRET', '')
        self.access_token = os.getenv('WEIBO_ACCESS_TOKEN', '')
        
        # 微博开放平台API基础URL
        self.api_base_url = 'https://api.weibo.com/2'
        
        # 微博API接口
        # 参考: https://open.weibo.com/wiki/2/statuses/show
        self.statuses_show_api = f'{self.api_base_url}/statuses/show.json'
        # 参考: https://open.weibo.com/wiki/2/statuses/user_timeline
        self.user_timeline_api = f'{self.api_base_url}/statuses/user_timeline.json'
        # 参考: https://open.weibo.com/wiki/2/comments/show
        self.comments_show_api = f'{self.api_base_url}/comments/show.json'
        
        # 移动端API（作为备用方案）
        self.mobile_search_api = 'https://m.weibo.cn/api/container/getIndex'
    
    def get_platform_name(self) -> str:
        return "微博"
    
    def is_available(self) -> bool:
        """检查是否可用
        
        如果有access_token，使用官方API；否则使用移动端API
        """
        return True  # 移动端API始终可用，官方API需要access_token
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """采集微博问题"""
        questions = []
        
        try:
            # 使用真实API采集
            questions = self._collect_from_api(config)
            print(f"[微博采集器] 成功采集到 {len(questions)} 个问题")
        except Exception as e:
            import traceback
            print(f"[微博采集器] 采集失败: {str(e)}")
            print(f"[微博采集器] 错误详情: {traceback.format_exc()}")
            # API失败时返回空列表，不降级到模拟数据
            questions = []
        
        return questions
    
    def _collect_from_api(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """从真实API采集
        
        优先使用微博开放平台官方API，如果没有access_token则使用移动端API
        """
        questions = []
        
        # 如果配置了access_token，尝试使用官方API
        if self.access_token:
            try:
                questions = self._collect_from_official_api(config)
                if questions:
                    print(f"[微博采集器] 使用官方API采集到 {len(questions)} 个问题")
                    return questions
            except Exception as e:
                print(f"[微博采集器] 官方API采集失败，降级到移动端API: {str(e)}")
        
        # 使用移动端API（备用方案）
        try:
            questions = self._collect_from_mobile_api(config)
            print(f"[微博采集器] 使用移动端API采集到 {len(questions)} 个问题")
        except Exception as e:
            print(f"[微博采集器] 移动端API采集失败: {str(e)}")
        
        return questions
    
    def _collect_from_official_api(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """使用微博开放平台官方API采集
        
        参考: https://open.weibo.com/wiki/微博API
        注意: 官方API主要用于获取授权用户的数据，对于公开搜索可能需要使用其他方式
        """
        questions = []
        
        # 注意：微博开放平台的标准API主要用于获取授权用户的时间线
        # 对于关键词搜索，可能需要使用商业接口或移动端API
        # 这里实现一个基于用户时间线的采集方案
        
        # 如果有关键词，尝试从用户时间线中筛选
        # 注意：这需要授权用户的时间线权限
        
        print(f"[微博采集器] 使用官方API采集（需要access_token）")
        
        # 这里可以实现基于用户时间线的采集
        # 由于官方API的搜索功能有限，建议使用移动端API或商业接口
        
        return questions
    
    def _collect_from_mobile_api(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """使用移动端API采集（公开接口，无需认证）"""
        questions = []
        
        try:
            # 微博搜索使用话题标签格式
            topic_keyword = f"#{config.topic}#"
            
            # 使用移动端API搜索（公开接口）
            self.rate_limiter.wait_if_needed()
            
            # 搜索参数
            search_params = {
                'containerid': f'100103type=1&q={config.topic}',
                'page_type': 'searchall',
                'page': 1
            }
            
            print(f"[微博采集器] 使用移动端API搜索主题: {config.topic}")
            response = self.http_client.get(self.mobile_search_api, params=search_params)
            
            if response.status_code != 200:
                print(f"[微博采集器] 移动端搜索API返回状态码: {response.status_code}")
                return questions
            
            data = response.json()
            cards = data.get('data', {}).get('cards', [])
            
            print(f"[微博采集器] 搜索到 {len(cards)} 个卡片")
            
            # 解析卡片数据
            for card in cards:
                if card.get('card_type') != 9:  # 9表示微博内容卡片
                    continue
                
                mblog = card.get('mblog', {})
                if not mblog:
                    continue
                
                # 检查是否包含主题关键词
                text = mblog.get('text', '')
                if config.topic not in text and topic_keyword not in text:
                    continue
                
                # 提取问题内容
                title = mblog.get('title', '')
                if not title:
                    # 如果没有标题，使用文本前100个字符作为标题
                    import re
                    # 去除HTML标签
                    text_clean = re.sub(r'<[^>]+>', '', text)
                    title = text_clean[:100] if len(text_clean) > 100 else text_clean
                
                content = text
                # 清理HTML标签
                import re
                content = re.sub(r'<[^>]+>', '', content)
                content = content.replace('&nbsp;', ' ').strip()
                
                # 采集回答（评论）
                answers = []
                if config.collect_answers:
                    # 优先使用官方API获取评论
                    if self.access_token:
                        try:
                            answers = self._collect_comments_from_official_api(mblog.get('id'), config)
                        except:
                            # 如果官方API失败，使用移动端API
                            answers = self._collect_comments_from_mobile_api(mblog.get('id'), config)
                    else:
                        answers = self._collect_comments_from_mobile_api(mblog.get('id'), config)
                
                # 创建问题对象
                created_at = datetime.now()
                created_str = mblog.get('created_at', '')
                if created_str:
                    try:
                        # 微博时间格式: "Mon Oct 10 10:00:00 +0800 2024"
                        # 尝试使用dateutil解析，如果不可用则使用datetime.strptime
                        try:
                            from dateutil import parser
                            created_at = parser.parse(created_str)
                        except ImportError:
                            # 如果没有dateutil，使用简单的字符串解析
                            from datetime import datetime
                            # 尝试解析常见格式
                            try:
                                created_at = datetime.strptime(created_str, '%a %b %d %H:%M:%S %z %Y')
                            except:
                                created_at = datetime.now()
                    except:
                        created_at = datetime.now()
                
                question = CollectedQuestion(
                    title=title or f'关于{config.topic}的讨论',
                    content=content,
                    source=self.get_platform_name(),
                    source_url=f"https://weibo.com/{mblog.get('user', {}).get('id', '')}/{mblog.get('bid', '')}",
                    author=mblog.get('user', {}).get('screen_name', '微博用户'),
                    created_at=created_at,
                    tags=[config.topic],
                    metadata={
                        'weibo_id': mblog.get('id'),
                        'reposts_count': mblog.get('reposts_count', 0),
                        'comments_count': mblog.get('comments_count', 0),
                        'attitudes_count': mblog.get('attitudes_count', 0)
                    },
                    answers=answers
                )
                questions.append(question)
                
                if len(questions) >= config.max_results:
                    break
                    
        except Exception as e:
            import traceback
            print(f"[微博采集器] API调用异常: {str(e)}")
            print(f"[微博采集器] 异常详情: {traceback.format_exc()}")
        
        return questions
    
    def _collect_comments_from_official_api(self, weibo_id: str, config: CollectionConfig) -> List[CollectedAnswer]:
        """使用微博开放平台官方API采集评论
        
        参考: https://open.weibo.com/wiki/2/comments/show
        """
        answers = []
        
        try:
            self.rate_limiter.wait_if_needed()
            
            # 获取评论列表
            params = {
                'access_token': self.access_token,
                'id': weibo_id,
                'count': min(config.max_answers_per_question * 3, 50),
                'page': 1
            }
            
            response = self.http_client.get(self.comments_show_api, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查是否有错误
                if 'error' in data:
                    print(f"[微博采集器] 官方API返回错误: {data.get('error', '未知错误')}")
                    return answers
                
                comments = data.get('comments', [])
                
                for comment_data in comments:
                    # 提取评论信息
                    like_count = comment_data.get('attitudes_count', 0)
                    
                    # 过滤低点赞数评论
                    if like_count < config.min_answer_upvotes:
                        continue
                    
                    text = comment_data.get('text', '')
                    # 清理HTML标签
                    import re
                    text = re.sub(r'<[^>]+>', '', text)
                    text = text.replace('&nbsp;', ' ').strip()
                    
                    if not text:
                        continue
                    
                    user = comment_data.get('user', {})
                    author_name = user.get('screen_name', '匿名用户')
                    
                    # 解析时间
                    created_at = datetime.now()
                    created_str = comment_data.get('created_at', '')
                    if created_str:
                        try:
                            from dateutil import parser
                            created_at = parser.parse(created_str)
                        except:
                            try:
                                from datetime import datetime
                                created_at = datetime.strptime(created_str, '%a %b %d %H:%M:%S %z %Y')
                            except:
                                pass
                    
                    answer = CollectedAnswer(
                        content=text,
                        author=author_name,
                        upvotes=like_count,
                        downvotes=0,
                        source_url=f"https://weibo.com/comment/{comment_data.get('id', '')}",
                        created_at=created_at,
                        metadata={
                            'weibo_comment_id': comment_data.get('id'),
                            'official_api': True
                        }
                    )
                    answers.append(answer)
                    
                    if len(answers) >= config.max_answers_per_question:
                        break
                
                # 按点赞数排序
                answers.sort(key=lambda a: a.upvotes, reverse=True)
                
        except Exception as e:
            print(f"[微博采集器] 使用官方API采集评论失败: {str(e)}")
        
        return answers
    
    def _collect_comments_from_mobile_api(self, weibo_id: str, config: CollectionConfig) -> List[CollectedAnswer]:
        """采集微博的评论（作为回答）"""
        answers = []
        
        try:
            self.rate_limiter.wait_if_needed()
            
            # 获取评论API
            comment_api = f'https://m.weibo.cn/comments/hotflow'
            params = {
                'id': weibo_id,
                'mid': weibo_id,
                'max_id_type': 0
            }
            
            response = self.http_client.get(comment_api, params=params)
            
            if response.status_code == 200:
                data = response.json()
                comments = data.get('data', [])
                
                for comment_data in comments:
                    like_count = comment_data.get('like_count', 0)
                    
                    # 过滤低点赞数评论
                    if like_count < config.min_answer_upvotes:
                        continue
                    
                    text = comment_data.get('text', '')
                    # 清理HTML标签
                    import re
                    text = re.sub(r'<[^>]+>', '', text)
                    text = text.replace('&nbsp;', ' ').strip()
                    
                    if not text:
                        continue
                    
                    user = comment_data.get('user', {})
                    author_name = user.get('screen_name', '匿名用户')
                    
                    created_at = datetime.now()
                    created_str = comment_data.get('created_at', '')
                    if created_str:
                        try:
                            # 尝试使用dateutil解析，如果不可用则使用datetime.strptime
                            try:
                                from dateutil import parser
                                created_at = parser.parse(created_str)
                            except ImportError:
                                # 如果没有dateutil，使用简单的字符串解析
                                from datetime import datetime
                                try:
                                    created_at = datetime.strptime(created_str, '%a %b %d %H:%M:%S %z %Y')
                                except:
                                    created_at = datetime.now()
                        except:
                            created_at = datetime.now()
                    
                    answer = CollectedAnswer(
                        content=text,
                        author=author_name,
                        upvotes=like_count,
                        downvotes=0,  # 微博评论没有点踩
                        source_url=f"https://m.weibo.cn/comment/{comment_data.get('id', '')}",
                        created_at=created_at,
                        metadata={
                            'weibo_comment_id': comment_data.get('id'),
                            'reply_count': comment_data.get('total_number', 0)
                        }
                    )
                    answers.append(answer)
                    
                    if len(answers) >= config.max_answers_per_question:
                        break
                
                # 按点赞数排序
                answers.sort(key=lambda a: a.upvotes, reverse=True)
                
        except Exception as e:
            print(f"[微博采集器] 采集评论失败: {str(e)}")
        
        return answers

