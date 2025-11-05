"""
微信热搜采集器
使用聚合数据的微信热搜API获取热点话题
参考: https://www.juhe.cn/docs/api/id/737
"""
from typing import List
from backend.collectors.interfaces import (
    CollectedQuestion, CollectionConfig, QuestionCollector
)
from backend.collectors.collectors.base_collector import HTTPClient, RateLimiter
from backend.config import Config
from datetime import datetime
import os
import json


class WeixinHotCollector:
    """微信热搜采集器
    
    使用聚合数据的微信热搜API获取热点话题
    接口文档: https://www.juhe.cn/docs/api/id/737
    """
    
    def __init__(self):
        # 组合HTTP客户端
        self.http_client = HTTPClient(timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        # 组合速率限制器（聚合数据免费版50次/天）
        self.rate_limiter = RateLimiter(requests_per_second=0.5)
        
        # 聚合数据API配置
        # 接口地址: http://apis.juhe.cn/fapigx/wxhottopic/query
        self.api_url = 'http://apis.juhe.cn/fapigx/wxhottopic/query'
        # 从配置文件读取API密钥
        self.api_key = Config.JUHE_API_KEY
    
    def get_platform_name(self) -> str:
        """获取平台名称"""
        return "微信热搜"
    
    def is_available(self) -> bool:
        """检查是否可用（需要配置API密钥）"""
        return bool(self.api_key)
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """采集微信热搜话题
        
        注意：微信热搜API返回的是热点话题，不是问题
        这里将热搜话题转换为问题格式，内容可以根据话题生成
        """
        print(f"[微信热搜采集器] ========== 开始采集 ==========")
        print(f"[微信热搜采集器] 配置: topic={config.topic}, max_results={config.max_results}, platform={config.platform}")
        print(f"[微信热搜采集器] API密钥已配置: {bool(self.api_key)}")
        
        questions = []
        
        try:
            # 使用聚合数据API采集
            questions = self._collect_from_api(config)
            print(f"[微信热搜采集器] 成功采集到 {len(questions)} 个热搜话题")
            print(f"[微信热搜采集器] ========== 采集完成 ==========")
        except Exception as e:
            import traceback
            print(f"[微信热搜采集器] 采集失败: {str(e)}")
            print(f"[微信热搜采集器] 错误详情: {traceback.format_exc()}")
            questions = []
        
        return questions
    
    def _collect_from_api(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """从聚合数据API采集"""
        questions = []
        
        if not self.api_key:
            print("[微信热搜采集器] 错误: 未配置聚合数据API密钥 (JUHE_API_KEY)")
            return questions
        
        try:
            self.rate_limiter.wait_if_needed()
            
            # 构建请求参数
            # 参考文档: https://www.juhe.cn/docs/api/id/737
            params = {
                'key': self.api_key
            }
            
            print(f"[微信热搜采集器] 请求微信热搜API: {self.api_url}")
            print(f"[微信热搜采集器] 请求参数: key={self.api_key[:10]}...")
            response = self.http_client.get(self.api_url, params=params)
            
            print(f"[微信热搜采集器] API响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[微信热搜采集器] API返回状态码错误: {response.status_code}")
                print(f"[微信热搜采集器] 响应内容: {response.text[:500]}")
                return questions
            
            try:
                data = response.json()
            except Exception as e:
                print(f"[微信热搜采集器] JSON解析失败: {str(e)}")
                print(f"[微信热搜采集器] 响应内容: {response.text[:500]}")
                return questions
            
            print(f"[微信热搜采集器] API返回数据: {json.dumps(data, ensure_ascii=False)[:500]}...")
            
            # 检查错误码
            error_code = data.get('error_code', -1)
            if error_code != 0:
                reason = data.get('reason', '未知错误')
                print(f"[微信热搜采集器] API返回错误: error_code={error_code}, reason={reason}")
                return questions
            
            # 解析结果
            result = data.get('result', {})
            if not result:
                print(f"[微信热搜采集器] 警告: result字段为空或不存在")
                print(f"[微信热搜采集器] 完整响应数据: {json.dumps(data, ensure_ascii=False)[:1000]}")
                return questions
            
            hot_list = result.get('list', [])
            
            if not hot_list:
                print(f"[微信热搜采集器] 警告: list字段为空或不存在")
                print(f"[微信热搜采集器] result内容: {json.dumps(result, ensure_ascii=False)[:1000]}")
                return questions
            
            print(f"[微信热搜采集器] 获取到 {len(hot_list)} 个热搜话题")
            
            # 调试：打印第一个热搜项的完整字段，查看API返回的所有数据
            if hot_list:
                print(f"[微信热搜采集器] 调试：第一个热搜项的完整字段:")
                print(json.dumps(hot_list[0], ensure_ascii=False, indent=2))
            
            # 将热搜话题转换为问题
            # 注意：微信热搜返回的是当前热点话题，可能不包含用户输入的主题
            # 如果用户输入了主题，优先返回包含该主题的话题；否则返回所有热搜
            matched_items = []
            other_items = []
            
            # 检查是否有有效的主题（非空字符串）
            has_topic = bool(config.topic and config.topic.strip())
            
            for item in hot_list:
                topic_word = item.get('word', '').strip()
                index = item.get('index', 0)
                
                if not topic_word:
                    continue
                
                # 如果配置了主题，优先匹配相关话题
                if has_topic:
                    topic_lower = config.topic.strip().lower()
                    word_lower = topic_word.lower()
                    # 更灵活的匹配：包含关键词或关键词包含在话题中
                    if topic_lower in word_lower or word_lower in topic_lower:
                        matched_items.append((item, index))
                    else:
                        other_items.append((item, index))
                else:
                    # 没有主题限制，全部添加
                    matched_items.append((item, index))
            
            # 优先使用匹配的话题，如果不够再补充其他话题
            # 注意：如果用户指定了主题但没有匹配的话题，仍然返回其他话题（避免完全无数据）
            items_to_use = matched_items[:config.max_results]
            if len(items_to_use) < config.max_results:
                remaining = config.max_results - len(items_to_use)
                items_to_use.extend(other_items[:remaining])
            
            # 如果用户指定了主题但没有匹配的话题，给出提示
            if has_topic and len(matched_items) == 0 and len(other_items) > 0:
                print(f"[微信热搜采集器] 提示: 未找到包含主题 '{config.topic}' 的话题，返回其他热搜话题")
            
            print(f"[微信热搜采集器] 准备处理 {len(items_to_use)} 个热搜话题")
            
            for item, index in items_to_use:
                topic_word = item.get('word', '').strip()
                
                if not topic_word:
                    print(f"[微信热搜采集器] 跳过空话题，索引: {index}")
                    continue
                
                # 尝试获取所有可能的字段
                # 常见字段：word(话题词), index(排名), url(链接), content(内容), desc(描述), etc.
                source_url = item.get('url') or item.get('link') or item.get('href')
                article_content = item.get('content') or item.get('desc') or item.get('description') or item.get('text')
                
                # 将热搜话题转换为问题格式
                # 热搜话题通常是短语，可以转换为问题标题
                # 确保标题长度足够，避免被过滤器过滤
                question_title = f"关于{topic_word}的讨论"
                
                # 如果有文章内容，使用文章内容；否则使用默认描述
                # 确保内容长度足够（至少10个字符），避免被MinLengthFilter过滤
                if article_content:
                    question_content = f"微信热搜话题：{topic_word}\n\n{article_content}\n\n这是当前微信公众平台的热点话题，排名第{index + 1}位。"
                else:
                    # 确保内容足够长，避免被过滤器过滤
                    question_content = f"微信热搜话题：{topic_word}。这是当前微信公众平台的热点话题，排名第{index + 1}位。话题在微信公众平台热度较高，值得关注和讨论。"
                
                print(f"[微信热搜采集器] 处理话题: {topic_word}, 标题长度: {len(question_title)}, 内容长度: {len(question_content)}")
                
                # 保存所有原始字段到metadata中
                metadata = {
                    'hot_word': topic_word,
                    'hot_index': index,
                    'source_api': 'juhe',
                    'api_id': 737,
                    'raw_item': item  # 保存原始数据，便于后续查看所有字段
                }
                
                question = CollectedQuestion(
                    title=question_title,
                    content=question_content,
                    source=self.get_platform_name(),
                    source_url=source_url,  # 如果有链接，使用链接
                    author=None,
                    created_at=datetime.now(),
                    tags=[config.topic] if config.topic else ['微信热搜', topic_word],
                    metadata=metadata,
                    answers=[]  # 微信热搜API不提供回答数据
                )
                
                questions.append(question)
            
            # 按热搜指数排序（index越大越热门）
            questions.sort(key=lambda q: q.metadata.get('hot_index', 0), reverse=True)
            
        except Exception as e:
            import traceback
            print(f"[微信热搜采集器] API调用异常: {str(e)}")
            print(f"[微信热搜采集器] 异常详情: {traceback.format_exc()}")
        
        return questions

