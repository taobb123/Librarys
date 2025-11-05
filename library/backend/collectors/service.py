"""
采集服务层
组合采集器管理器、数据处理器和问题模型
"""
from typing import List, Optional
from backend.collectors.interfaces import CollectionConfig, CollectedQuestion
from backend.collectors.collector_manager import CollectorManager
from backend.collectors.processors import (
    QuestionProcessor, MinLengthFilter, ContentQualityFilter
)
from backend.collectors.answer_scorers import DefaultAnswerScorer
from backend.collectors.collectors.zhihu_collector import ZhihuCollector
from backend.collectors.collectors.weibo_collector import WeiboCollector
import backend.models.problem_model as problem_model


class CollectionService:
    """采集服务
    
    使用组合模式组合各个组件
    """
    
    def __init__(self, problem_model_module=None, use_third_party: bool = False):
        """初始化服务，组合各个组件
        
        Args:
            problem_model_module: 问题数据模型模块
            use_third_party: 是否使用第三方API聚合平台
        """
        self.problem_model = problem_model_module or problem_model
        
        # 组合采集器
        collectors = []
        
        if use_third_party:
            # 使用第三方API聚合平台
            from backend.collectors.collectors.third_party_collector import (
                create_juhe_collector, create_showapi_collector, create_custom_collector
            )
            import os
            
            # 尝试创建第三方API采集器
            zhihu_api_key = os.getenv('ZHIHU_JUHE_API_KEY', '')
            weibo_api_key = os.getenv('WEIBO_JUHE_API_KEY', '')
            
            if zhihu_api_key:
                from backend.collectors.collectors.third_party_config import get_third_party_config
                zhihu_config = get_third_party_config('zhihu', 'juhe')
                collectors.append(create_juhe_collector('知乎', zhihu_api_key, zhihu_config))
                print("[采集服务] 使用第三方API: 知乎（聚合数据）")
            else:
                collectors.append(ZhihuCollector())
                print("[采集服务] 使用直接API: 知乎")
            
            if weibo_api_key:
                from backend.collectors.collectors.third_party_config import get_third_party_config
                weibo_config = get_third_party_config('weibo', 'juhe')
                collectors.append(create_juhe_collector('微博', weibo_api_key, weibo_config))
                print("[采集服务] 使用第三方API: 微博（聚合数据）")
            else:
                collectors.append(WeiboCollector())
                print("[采集服务] 使用直接API: 微博")
        else:
            # 使用直接API
            collectors = [
                ZhihuCollector(),
                WeiboCollector()
            ]
        
        # 添加微信热搜采集器（如果配置了聚合数据API密钥）
        from backend.collectors.collectors.weixin_hot_collector import WeixinHotCollector
        weixin_collector = WeixinHotCollector()
        if weixin_collector.is_available():
            collectors.append(weixin_collector)
            print("[采集服务] 启用微信热搜采集器（聚合数据）")
        
        # 组合数据处理器
        processor = QuestionProcessor(
            filters=[
                MinLengthFilter(min_title_length=5, min_content_length=10),
                ContentQualityFilter()
            ]
        )
        
        # 组合去重检查器
        from backend.collectors.processors import DatabaseDuplicateChecker
        duplicate_checker = DatabaseDuplicateChecker(self.problem_model)
        
        # 组合回答质量评分器
        self.answer_scorer = DefaultAnswerScorer(min_upvotes=10)
        
        # 组合管理器
        self.manager = CollectorManager(
            collectors=collectors,
            processor=processor,
            duplicate_checker=duplicate_checker
        )
    
    def collect_questions(self, 
                         topic: str,
                         max_results: int = 50,
                         platform: Optional[str] = None,
                         auto_save: bool = False,
                         collect_answers: bool = True,
                         max_answers_per_question: int = 3,
                         min_answer_upvotes: int = 10) -> dict:
        """采集问题
        
        Args:
            topic: 主题，如"股票"
            max_results: 最大采集数量
            platform: 指定平台，None表示所有平台
            auto_save: 是否自动保存到数据库
            collect_answers: 是否采集回答
            max_answers_per_question: 每个问题最多采集的回答数
            min_answer_upvotes: 回答最小点赞数要求
            
        Returns:
            包含采集结果和统计信息的字典
        """
        config = CollectionConfig(
            topic=topic,
            max_results=max_results,
            platform=platform,
            collect_answers=collect_answers,
            max_answers_per_question=max_answers_per_question,
            min_answer_upvotes=min_answer_upvotes
        )
        
        # 执行采集
        print(f"[采集服务] 开始采集主题: {topic}, 最大数量: {max_results}, 平台: {platform or '全部'}")
        questions = self.manager.collect(config)
        print(f"[采集服务] 采集完成，获得 {len(questions)} 个问题")
        
        # 处理回答：评分和排序
        total_answers = 0
        for question in questions:
            if question.answers:
                # 对每个回答进行质量评分
                for answer in question.answers:
                    answer.quality_score = self.answer_scorer.score(answer)
                
                # 按质量评分和点赞数排序，取前N个
                question.answers.sort(
                    key=lambda a: (a.quality_score, a.upvotes),
                    reverse=True
                )
                question.answers = question.answers[:max_answers_per_question]
                total_answers += len(question.answers)
        
        # 转换为问题数据格式
        saved_count = 0
        saved_answers_count = 0
        if auto_save and questions:
            saved_count, saved_answers_count = self._save_questions_with_answers(
                questions, topic
            )
        
        return {
            'success': True,
            'total_collected': len(questions),
            'total_answers_collected': total_answers,
            'saved': saved_count,
            'saved_answers': saved_answers_count,
            'questions': [
                {
                    'title': q.title,
                    'content': q.content,
                    'source': q.source,
                    'source_url': q.source_url,
                    'author': q.author,
                    'tags': q.tags + [topic] if topic not in q.tags else q.tags,
                    'category': self._guess_category(topic),
                    'answers': [
                        {
                            'content': a.content,
                            'author': a.author,
                            'upvotes': a.upvotes,
                            'downvotes': a.downvotes,
                            'quality_score': round(a.quality_score, 3),
                            'source_url': a.source_url
                        }
                        for a in q.answers
                    ],
                    'metadata': {
                        'collected_at': q.created_at.isoformat() if q.created_at else None,
                        'source_metadata': q.metadata
                    }
                }
                for q in questions
            ]
        }
    
    def _save_questions_with_answers(self, questions: List[CollectedQuestion], topic: str) -> tuple:
        """保存问题和回答到数据库
        
        Returns:
            (保存的问题数, 保存的回答数)
        """
        saved_count = 0
        saved_answers_count = 0
        category = self._guess_category(topic)
        
        # 导入回答模型
        try:
            import backend.models.answer_model as answer_model
        except ImportError:
            # 如果回答模型不存在，只保存问题
            answer_model = None
        
        for question in questions:
            try:
                # 检查是否已存在（通过标题）
                existing_problems = self.problem_model.get_all_problems()
                title_normalized = question.title.lower().strip()
                
                # 简单去重检查
                is_duplicate = any(
                    p.get('title', '').lower().strip() == title_normalized
                    for p in existing_problems
                )
                
                if not is_duplicate:
                    # 保存问题
                    problem_id = self.problem_model.add_problem(
                        title=question.title,
                        content=question.content,
                        category=category,
                        tags=question.tags + [topic] if topic not in question.tags else question.tags
                    )
                    saved_count += 1
                    
                    # 保存回答（如果存在回答模型）
                    if answer_model and question.answers:
                        for answer in question.answers:
                            try:
                                answer_model.add_answer(
                                    problem_id=problem_id,
                                    content=answer.content,
                                    author=answer.author,
                                    upvotes=answer.upvotes,
                                    downvotes=answer.downvotes,
                                    quality_score=answer.quality_score,
                                    source_url=answer.source_url
                                )
                                saved_answers_count += 1
                            except Exception as e:
                                print(f"保存回答失败: {str(e)}")
            except Exception as e:
                print(f"保存问题失败: {question.title}, 错误: {str(e)}")
        
        return saved_count, saved_answers_count
    
    def _guess_category(self, topic: str) -> str:
        """根据主题猜测分类"""
        category_map = {
            '股票': '金融',
            '基金': '金融',
            '投资': '金融',
            '科技': '科技',
            '人工智能': '科技',
            '文学': '文学',
            '历史': '历史',
            '艺术': '艺术'
        }
        
        for key, category in category_map.items():
            if key in topic:
                return category
        
        return '其他'
    
    def get_available_platforms(self) -> List[str]:
        """获取可用的采集平台"""
        return self.manager.get_available_collectors()
    
    def get_all_platforms(self) -> List[str]:
        """获取所有采集平台列表（包括不可用的）"""
        return self.manager.get_all_collectors()

