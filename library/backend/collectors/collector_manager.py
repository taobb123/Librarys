"""
采集器管理器
使用组合模式管理多个采集器
"""
from typing import List, Dict, Optional
from backend.collectors.interfaces import (
    QuestionCollector, CollectionConfig, CollectedQuestion,
    DataProcessor, DuplicateChecker
)


class CollectorManager:
    """采集器管理器
    
    使用组合模式：
    - 组合多个采集器（而不是继承）
    - 组合数据处理器
    - 组合去重检查器
    """
    
    def __init__(self, 
                 collectors: List[QuestionCollector] = None,
                 processor: Optional[DataProcessor] = None,
                 duplicate_checker: Optional[DuplicateChecker] = None):
        """
        初始化管理器
        
        Args:
            collectors: 采集器列表（可组合）
            processor: 数据处理器（可组合）
            duplicate_checker: 去重检查器（可组合）
        """
        self.collectors: Dict[str, QuestionCollector] = {}
        if collectors:
            for collector in collectors:
                self.register_collector(collector)
        
        # 组合数据处理器
        self.processor = processor
        
        # 组合去重检查器
        self.duplicate_checker = duplicate_checker
    
    def register_collector(self, collector: QuestionCollector) -> None:
        """注册采集器"""
        platform_name = collector.get_platform_name()
        self.collectors[platform_name] = collector
    
    def get_collector(self, platform_name: str) -> Optional[QuestionCollector]:
        """获取指定平台的采集器"""
        return self.collectors.get(platform_name)
    
    def get_available_collectors(self) -> List[str]:
        """获取所有可用的采集器平台名称"""
        return [name for name, collector in self.collectors.items() 
                if collector.is_available()]
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """执行采集
        
        使用组合的采集器、处理器和去重检查器
        """
        all_questions = []
        
        # 确定要使用的采集器
        collectors_to_use = []
        if config.platform:
            # 指定了平台
            collector = self.collectors.get(config.platform)
            if collector and collector.is_available():
                collectors_to_use = [collector]
        else:
            # 使用所有可用采集器
            collectors_to_use = [c for c in self.collectors.values() 
                                if c.is_available()]
        
        # 执行采集
        for collector in collectors_to_use:
            try:
                questions = collector.collect(config)
                all_questions.extend(questions)
            except Exception as e:
                print(f"采集器 {collector.get_platform_name()} 采集失败: {str(e)}")
        
        # 应用数据处理器（如果配置了）
        if self.processor:
            all_questions = self.processor.process(all_questions)
        
        # 去重（如果配置了去重检查器）
        if self.duplicate_checker:
            unique_questions = []
            for question in all_questions:
                if not self.duplicate_checker.is_duplicate(question):
                    self.duplicate_checker.mark_as_seen(question)
                    unique_questions.append(question)
            all_questions = unique_questions
        
        # 限制返回数量
        return all_questions[:config.max_results]

