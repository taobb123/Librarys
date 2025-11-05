"""
微博采集器实现
"""
from typing import List
from backend.collectors.interfaces import CollectedQuestion, CollectionConfig, QuestionCollector
from backend.collectors.collectors.base_collector import HTTPClient, RateLimiter
from datetime import datetime
import os


class WeiboCollector:
    """微博问题采集器"""
    
    def __init__(self):
        self.http_client = HTTPClient(timeout=30)
        self.rate_limiter = RateLimiter(requests_per_second=0.3)
        self.api_key = os.getenv('WEIBO_API_KEY', '')
    
    def get_platform_name(self) -> str:
        return "微博"
    
    def is_available(self) -> bool:
        return True
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """采集微博问题"""
        # 微博通常使用话题标签，这里模拟采集
        questions = []
        
        mock_questions = [
            {
                'title': f'#{config.topic}# 最近有什么值得关注的吗？',
                'content': f'关于{config.topic}，最近有什么值得关注的新动态？',
                'author': '微博用户'
            },
            {
                'title': f'#{config.topic}# 投资需要注意什么？',
                'content': f'{config.topic}投资有什么需要注意的地方？',
                'author': '微博用户'
            },
            {
                'title': f'#{config.topic}# 小白求指导',
                'content': f'刚接触{config.topic}，求各位大佬指导一下入门知识。',
                'author': '微博用户'
            }
        ]
        
        for i, q in enumerate(mock_questions[:config.max_results]):
            questions.append(CollectedQuestion(
                title=q['title'],
                content=q['content'],
                source=self.get_platform_name(),
                source_url=f"https://weibo.com/mock_{i}",
                author=q['author'],
                created_at=datetime.now(),
                tags=[config.topic],
                metadata={'mock': True}
            ))
        
        return questions

