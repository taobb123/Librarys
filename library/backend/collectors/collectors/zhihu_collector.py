"""
知乎采集器实现
使用组合模式，组合HTTP客户端和速率限制器
"""
from typing import List
from backend.collectors.interfaces import CollectedQuestion, CollectionConfig, QuestionCollector
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
        self.http_client = HTTPClient(timeout=30)
        # 组合速率限制器
        self.rate_limiter = RateLimiter(requests_per_second=0.5)
        self.api_key = os.getenv('ZHIHU_API_KEY', '')
        self.api_url = os.getenv('ZHIHU_API_URL', 'https://www.zhihu.com/api/v4/search_v3')
    
    def get_platform_name(self) -> str:
        """获取平台名称"""
        return "知乎"
    
    def is_available(self) -> bool:
        """检查是否可用"""
        # 如果没有配置API，使用模拟数据
        return True
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """采集知乎问题"""
        questions = []
        
        try:
            # 如果有API配置，使用真实API
            if self.api_key:
                questions = self._collect_from_api(config)
            else:
                # 否则使用模拟数据（用于演示）
                questions = self._collect_mock_data(config)
        except Exception as e:
            print(f"知乎采集失败: {str(e)}")
            # 如果API失败，使用模拟数据作为降级方案
            questions = self._collect_mock_data(config)
        
        return questions
    
    def _collect_from_api(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """从API采集"""
        questions = []
        self.rate_limiter.wait_if_needed()
        
        try:
            params = {
                'q': config.topic,
                't': 'question',
                'limit': min(config.max_results, 20),
                'offset': 0
            }
            
            response = self.http_client.get(self.api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', [])[:config.max_results]:
                    if item.get('object', {}).get('type') == 'question':
                        question_data = item['object']
                        questions.append(CollectedQuestion(
                            title=question_data.get('title', ''),
                            content=question_data.get('excerpt', ''),
                            source=self.get_platform_name(),
                            source_url=f"https://www.zhihu.com/question/{question_data.get('id', '')}",
                            author=question_data.get('author', {}).get('name'),
                            created_at=datetime.fromtimestamp(question_data.get('created_time', 0)),
                            tags=[config.topic],
                            metadata={'zhihu_id': question_data.get('id')}
                        ))
        except Exception as e:
            print(f"知乎API调用失败: {str(e)}")
        
        return questions
    
    def _collect_mock_data(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """生成模拟数据（用于演示和测试）"""
        mock_questions = [
            {
                'title': f'{config.topic}投资有哪些风险需要关注？',
                'content': f'关于{config.topic}投资，我们需要关注哪些主要风险？包括市场风险、流动性风险、信用风险等方面。',
                'author': '知乎用户'
            },
            {
                'title': f'如何评估{config.topic}的投资价值？',
                'content': f'评估{config.topic}投资价值需要考虑哪些因素？基本面分析、技术面分析、市场情绪等。',
                'author': '知乎用户'
            },
            {
                'title': f'{config.topic}市场的最新趋势是什么？',
                'content': f'当前{config.topic}市场的最新趋势分析，包括政策影响、市场情绪、资金流向等。',
                'author': '知乎用户'
            },
            {
                'title': f'新手如何开始{config.topic}投资？',
                'content': f'作为{config.topic}投资新手，应该从哪些方面入手？需要学习哪些基础知识？',
                'author': '知乎用户'
            },
            {
                'title': f'{config.topic}投资中的常见误区有哪些？',
                'content': f'在{config.topic}投资过程中，投资者容易陷入哪些误区？如何避免这些误区？',
                'author': '知乎用户'
            }
        ]
        
        questions = []
        for i, q in enumerate(mock_questions[:config.max_results]):
            questions.append(CollectedQuestion(
                title=q['title'],
                content=q['content'],
                source=self.get_platform_name(),
                source_url=f"https://www.zhihu.com/question/mock_{i}",
                author=q['author'],
                created_at=datetime.now(),
                tags=[config.topic],
                metadata={'mock': True}
            ))
        
        return questions

