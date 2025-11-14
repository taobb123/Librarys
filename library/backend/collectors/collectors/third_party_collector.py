"""
第三方API聚合平台采集器
支持多种API聚合平台，如聚合数据、ShowAPI等
"""
from typing import List, Dict, Optional
from backend.collectors.interfaces import (
    CollectedQuestion, CollectedAnswer, CollectionConfig, QuestionCollector
)
from backend.collectors.collectors.base_collector import HTTPClient, RateLimiter
from datetime import datetime
import os
import json


class ThirdPartyAPICollector:
    """第三方API聚合平台采集器基类
    
    支持多种API聚合平台：
    - 聚合数据 (juhe.cn)
    - ShowAPI
    - 易源API
    - 其他自定义API聚合平台
    """
    
    def __init__(self, platform_name: str, api_config: Dict):
        """
        Args:
            platform_name: 平台名称（如"知乎"、"微博"）
            api_config: API配置字典，包含：
                - provider: 聚合平台提供商（'juhe', 'showapi', 'custom'等）
                - base_url: API基础URL
                - api_key: API密钥
                - search_endpoint: 搜索接口路径
                - detail_endpoint: 详情接口路径（可选）
                - answer_endpoint: 回答接口路径（可选）
                - params_mapping: 参数映射（将CollectionConfig映射到API参数）
                - response_mapping: 响应映射（将API响应映射到CollectedQuestion）
        """
        self.platform_name = platform_name
        self.config = api_config
        
        # 组合HTTP客户端
        self.http_client = HTTPClient(
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        
        # 组合速率限制器（第三方API通常有更宽松的限制）
        self.rate_limiter = RateLimiter(requests_per_second=1.0)
        
        # 根据提供商设置默认配置
        self._setup_provider_config()
    
    def _setup_provider_config(self):
        """根据提供商设置默认配置"""
        provider = self.config.get('provider', 'custom')
        
        if provider == 'juhe':
            # 聚合数据平台配置
            if 'base_url' not in self.config:
                self.config['base_url'] = 'http://v.juhe.cn'
            if 'params_mapping' not in self.config:
                self.config['params_mapping'] = {
                    'topic': 'q',
                    'max_results': 'pagesize'
                }
        
        elif provider == 'showapi':
            # ShowAPI平台配置
            if 'base_url' not in self.config:
                self.config['base_url'] = 'https://route.showapi.com'
            if 'params_mapping' not in self.config:
                self.config['params_mapping'] = {
                    'topic': 'keyword',
                    'max_results': 'pageSize'
                }
    
    def get_platform_name(self) -> str:
        """获取平台名称"""
        return self.platform_name
    
    def is_available(self) -> bool:
        """检查是否可用（需要配置API密钥）"""
        api_key = self.config.get('api_key') or os.getenv(f'{self.platform_name.upper()}_API_KEY', '')
        return bool(api_key)
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """采集问题"""
        questions = []
        
        try:
            # 使用第三方API采集
            questions = self._collect_from_third_party_api(config)
            print(f"[{self.platform_name}第三方API] 成功采集到 {len(questions)} 个问题")
        except Exception as e:
            import traceback
            print(f"[{self.platform_name}第三方API] 采集失败: {str(e)}")
            print(f"[{self.platform_name}第三方API] 错误详情: {traceback.format_exc()}")
            questions = []
        
        return questions
    
    def _collect_from_third_party_api(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """从第三方API采集"""
        questions = []
        
        # 获取API密钥
        api_key = self.config.get('api_key') or os.getenv(f'{self.platform_name.upper()}_API_KEY', '')
        if not api_key:
            print(f"[{self.platform_name}第三方API] 错误: 未配置API密钥")
            return questions
        
        # 构建搜索请求
        self.rate_limiter.wait_if_needed()
        
        base_url = self.config.get('base_url', '')
        search_endpoint = self.config.get('search_endpoint', '')
        if not base_url or not search_endpoint:
            print(f"[{self.platform_name}第三方API] 错误: 未配置API端点")
            return questions
        
        search_url = f"{base_url.rstrip('/')}/{search_endpoint.lstrip('/')}"
        
        # 构建请求参数
        params = self._build_request_params(config, api_key)
        
        print(f"[{self.platform_name}第三方API] 请求URL: {search_url}")
        print(f"[{self.platform_name}第三方API] 请求参数: {params}")
        
        # 发送请求
        response = self.http_client.get(search_url, params=params)
        
        if response.status_code != 200:
            print(f"[{self.platform_name}第三方API] 请求失败，状态码: {response.status_code}")
            return questions
        
        # 解析响应
        try:
            data = response.json()
            questions = self._parse_response(data, config)
        except Exception as e:
            print(f"[{self.platform_name}第三方API] 解析响应失败: {str(e)}")
        
        return questions
    
    def _build_request_params(self, config: CollectionConfig, api_key: str) -> Dict:
        """构建请求参数"""
        params_mapping = self.config.get('params_mapping', {})
        provider = self.config.get('provider', 'custom')
        
        params = {}
        
        # 添加API密钥
        if provider == 'juhe':
            params['key'] = api_key
        elif provider == 'showapi':
            params['showapi_appid'] = api_key
            params['showapi_sign'] = self.config.get('api_secret', '')  # ShowAPI需要签名
        else:
            params['api_key'] = api_key
            if 'api_secret' in self.config:
                params['api_secret'] = self.config['api_secret']
        
        # 映射参数
        if 'topic' in params_mapping:
            params[params_mapping['topic']] = config.topic
        else:
            params['q'] = config.topic
        
        if 'max_results' in params_mapping:
            params[params_mapping['max_results']] = min(config.max_results, 50)
        else:
            params['limit'] = min(config.max_results, 50)
        
        # 添加其他自定义参数
        custom_params = self.config.get('custom_params', {})
        params.update(custom_params)
        
        return params
    
    def _parse_response(self, data: Dict, config: CollectionConfig) -> List[CollectedQuestion]:
        """解析API响应"""
        questions = []
        
        # 获取响应映射配置
        response_mapping = self.config.get('response_mapping', {})
        
        # 根据提供商解析响应
        provider = self.config.get('provider', 'custom')
        
        if provider == 'juhe':
            # 聚合数据格式: {"error_code": 0, "reason": "success", "result": {...}}
            if data.get('error_code') == 0:
                result = data.get('result', {})
                items = result.get('data', []) if isinstance(result, dict) else result
                if not isinstance(items, list):
                    items = [items] if items else []
                
                for item in items[:config.max_results]:
                    question = self._parse_item(item, config, response_mapping)
                    if question:
                        questions.append(question)
        
        elif provider == 'showapi':
            # ShowAPI格式: {"showapi_res_code": 0, "showapi_res_body": {...}}
            if data.get('showapi_res_code') == 0:
                body = data.get('showapi_res_body', {})
                items = body.get('list', body.get('data', []))
                if not isinstance(items, list):
                    items = [items] if items else []
                
                for item in items[:config.max_results]:
                    question = self._parse_item(item, config, response_mapping)
                    if question:
                        questions.append(question)
        
        else:
            # 自定义格式，使用响应映射
            items = self._extract_items_from_response(data, response_mapping)
            for item in items[:config.max_results]:
                question = self._parse_item(item, config, response_mapping)
                if question:
                    questions.append(question)
        
        return questions
    
    def _extract_items_from_response(self, data: Dict, mapping: Dict) -> List:
        """从响应中提取数据项列表"""
        items_path = mapping.get('items_path', 'data')
        
        # 支持点号分隔的路径，如 "result.data.list"
        paths = items_path.split('.')
        items = data
        for path in paths:
            if isinstance(items, dict):
                items = items.get(path, [])
            else:
                return []
        
        if not isinstance(items, list):
            items = [items] if items else []
        
        return items
    
    def _parse_item(self, item: Dict, config: CollectionConfig, mapping: Dict) -> Optional[CollectedQuestion]:
        """解析单个数据项"""
        try:
            # 获取字段映射
            field_mapping = mapping.get('fields', {})
            
            # 提取字段
            title = self._get_field(item, field_mapping.get('title', 'title'))
            content = self._get_field(item, field_mapping.get('content', 'content'))
            source_url = self._get_field(item, field_mapping.get('source_url', 'url'))
            author = self._get_field(item, field_mapping.get('author', 'author'))
            
            if not title:
                return None
            
            # 解析时间
            created_at = datetime.now()
            created_field = field_mapping.get('created_at', 'created_at')
            if created_field in item:
                try:
                    created_str = str(item[created_field])
                    # 尝试解析时间戳或时间字符串
                    if created_str.isdigit():
                        created_at = datetime.fromtimestamp(int(created_str))
                    else:
                        from dateutil import parser
                        created_at = parser.parse(created_str)
                except:
                    pass
            
            # 采集回答（如果配置要求）
            answers = []
            if config.collect_answers:
                answers = self._collect_answers_from_item(item, config, mapping)
            
            # 创建问题对象
            question = CollectedQuestion(
                title=str(title),
                content=str(content) if content else '',
                source=self.platform_name,
                source_url=str(source_url) if source_url else None,
                author=str(author) if author else None,
                created_at=created_at,
                tags=[config.topic],
                metadata={
                    'third_party_api': True,
                    'provider': self.config.get('provider', 'custom'),
                    'raw_item': item
                },
                answers=answers
            )
            
            return question
            
        except Exception as e:
            print(f"[{self.platform_name}第三方API] 解析数据项失败: {str(e)}")
            return None
    
    def _get_field(self, item: Dict, field_path: str) -> Optional[str]:
        """获取字段值，支持点号分隔的路径"""
        if not field_path:
            return None
        
        paths = field_path.split('.')
        value = item
        for path in paths:
            if isinstance(value, dict):
                value = value.get(path)
            else:
                return None
            if value is None:
                return None
        
        return str(value) if value is not None else None
    
    def _collect_answers_from_item(self, item: Dict, config: CollectionConfig, mapping: Dict) -> List[CollectedAnswer]:
        """从数据项中采集回答"""
        answers = []
        
        # 检查是否有回答数据
        answer_field = mapping.get('answers_field', 'answers')
        answer_items = item.get(answer_field, [])
        
        if not isinstance(answer_items, list):
            answer_items = [answer_items] if answer_items else []
        
        answer_field_mapping = mapping.get('answer_fields', {})
        
        for answer_item in answer_items[:config.max_answers_per_question * 2]:
            try:
                content = self._get_field(answer_item, answer_field_mapping.get('content', 'content'))
                author = self._get_field(answer_item, answer_field_mapping.get('author', 'author'))
                upvotes = int(self._get_field(answer_item, answer_field_mapping.get('upvotes', 'upvotes')) or 0)
                
                # 过滤低点赞数回答
                if upvotes < config.min_answer_upvotes:
                    continue
                
                if not content:
                    continue
                
                answer = CollectedAnswer(
                    content=str(content),
                    author=str(author) if author else None,
                    upvotes=upvotes,
                    downvotes=int(self._get_field(answer_item, answer_field_mapping.get('downvotes', 'downvotes')) or 0),
                    source_url=self._get_field(answer_item, answer_field_mapping.get('source_url', 'url')),
                    created_at=datetime.now(),
                    metadata={'third_party_api': True}
                )
                
                answers.append(answer)
                
                if len(answers) >= config.max_answers_per_question:
                    break
                    
            except Exception as e:
                print(f"[{self.platform_name}第三方API] 解析回答失败: {str(e)}")
        
        # 按点赞数排序
        answers.sort(key=lambda a: a.upvotes, reverse=True)
        
        return answers


def create_juhe_collector(platform_name: str, api_key: str, api_config: Dict = None) -> ThirdPartyAPICollector:
    """创建聚合数据平台采集器
    
    Args:
        platform_name: 平台名称
        api_key: 聚合数据API密钥
        api_config: 额外配置
        
    示例配置:
        api_config = {
            'search_endpoint': 'zhihu/search',
            'response_mapping': {
                'items_path': 'result.data',
                'fields': {
                    'title': 'title',
                    'content': 'excerpt',
                    'source_url': 'url'
                }
            }
        }
    """
    config = {
        'provider': 'juhe',
        'base_url': 'http://v.juhe.cn',
        'api_key': api_key,
        **(api_config or {})
    }
    
    return ThirdPartyAPICollector(platform_name, config)


def create_showapi_collector(platform_name: str, app_id: str, secret: str, api_config: Dict = None) -> ThirdPartyAPICollector:
    """创建ShowAPI平台采集器
    
    Args:
        platform_name: 平台名称
        app_id: ShowAPI应用ID
        secret: ShowAPI密钥
        api_config: 额外配置
    """
    config = {
        'provider': 'showapi',
        'base_url': 'https://route.showapi.com',
        'api_key': app_id,
        'api_secret': secret,
        **(api_config or {})
    }
    
    return ThirdPartyAPICollector(platform_name, config)


def create_custom_collector(platform_name: str, api_config: Dict) -> ThirdPartyAPICollector:
    """创建自定义API平台采集器
    
    Args:
        platform_name: 平台名称
        api_config: 完整配置字典，必须包含：
            - base_url: API基础URL
            - api_key: API密钥
            - search_endpoint: 搜索接口路径
            - response_mapping: 响应映射配置
    """
    config = {
        'provider': 'custom',
        **api_config
    }
    
    return ThirdPartyAPICollector(platform_name, config)






