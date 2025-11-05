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
from backend.collectors.collectors.zhihu_collector import ZhihuCollector
from backend.collectors.collectors.weibo_collector import WeiboCollector
import backend.models.problem_model as problem_model


class CollectionService:
    """采集服务
    
    使用组合模式组合各个组件
    """
    
    def __init__(self, problem_model_module=None):
        """初始化服务，组合各个组件"""
        self.problem_model = problem_model_module or problem_model
        
        # 组合采集器
        collectors = [
            ZhihuCollector(),
            WeiboCollector()
        ]
        
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
                         auto_save: bool = False) -> dict:
        """采集问题
        
        Args:
            topic: 主题，如"股票"
            max_results: 最大采集数量
            platform: 指定平台，None表示所有平台
            auto_save: 是否自动保存到数据库
            
        Returns:
            包含采集结果和统计信息的字典
        """
        config = CollectionConfig(
            topic=topic,
            max_results=max_results,
            platform=platform
        )
        
        # 执行采集
        questions = self.manager.collect(config)
        
        # 转换为问题数据格式
        saved_count = 0
        if auto_save and questions:
            saved_count = self._save_questions(questions, topic)
        
        return {
            'success': True,
            'total_collected': len(questions),
            'saved': saved_count,
            'questions': [
                {
                    'title': q.title,
                    'content': q.content,
                    'source': q.source,
                    'source_url': q.source_url,
                    'author': q.author,
                    'tags': q.tags + [topic] if topic not in q.tags else q.tags,
                    'category': self._guess_category(topic),
                    'metadata': {
                        'collected_at': q.created_at.isoformat() if q.created_at else None,
                        'source_metadata': q.metadata
                    }
                }
                for q in questions
            ]
        }
    
    def _save_questions(self, questions: List[CollectedQuestion], topic: str) -> int:
        """保存问题到数据库"""
        saved_count = 0
        category = self._guess_category(topic)
        
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
                    self.problem_model.add_problem(
                        title=question.title,
                        content=question.content,
                        category=category,
                        tags=question.tags + [topic] if topic not in question.tags else question.tags
                    )
                    saved_count += 1
            except Exception as e:
                print(f"保存问题失败: {question.title}, 错误: {str(e)}")
        
        return saved_count
    
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

