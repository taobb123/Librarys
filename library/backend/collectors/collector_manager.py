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
    
    def get_all_collectors(self) -> List[str]:
        """获取所有注册的采集器平台名称（包括不可用的）"""
        return list(self.collectors.keys())
    
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
            if collector:
                if collector.is_available():
                    collectors_to_use = [collector]
                    print(f"[采集管理器] 使用指定平台: {config.platform}")
                else:
                    print(f"[采集管理器] 警告: 平台 {config.platform} 不可用")
            else:
                print(f"[采集管理器] 警告: 未找到平台 {config.platform}")
        else:
            # 使用所有可用采集器
            collectors_to_use = [c for c in self.collectors.values() 
                                if c.is_available()]
            print(f"[采集管理器] 使用所有可用采集器: {len(collectors_to_use)} 个")
        
        if not collectors_to_use:
            print("[采集管理器] 错误: 没有可用的采集器")
            return []
        
        # 执行采集
        for collector in collectors_to_use:
            try:
                print(f"[采集管理器] 开始采集: {collector.get_platform_name()}")
                questions = collector.collect(config)
                print(f"[采集管理器] {collector.get_platform_name()} 采集到 {len(questions)} 个问题")
                all_questions.extend(questions)
            except Exception as e:
                import traceback
                print(f"[采集管理器] 采集器 {collector.get_platform_name()} 采集失败: {str(e)}")
                print(f"[采集管理器] 错误详情: {traceback.format_exc()}")
        
        print(f"[采集管理器] 采集阶段总计: {len(all_questions)} 个问题")
        
        # 应用数据处理器（如果配置了）
        if self.processor:
            before_count = len(all_questions)
            all_questions = self.processor.process(all_questions)
            after_count = len(all_questions)
            print(f"[采集管理器] 数据处理器: {before_count} -> {after_count} (过滤了 {before_count - after_count} 个)")
        
        # 去重（如果配置了去重检查器）
        if self.duplicate_checker:
            before_count = len(all_questions)
            unique_questions = []
            for question in all_questions:
                if not self.duplicate_checker.is_duplicate(question):
                    self.duplicate_checker.mark_as_seen(question)
                    unique_questions.append(question)
            all_questions = unique_questions
            after_count = len(all_questions)
            print(f"[采集管理器] 去重检查: {before_count} -> {after_count} (去重了 {before_count - after_count} 个)")
        
        # 限制返回数量
        result = all_questions[:config.max_results]
        print(f"[采集管理器] 最终返回: {len(result)} 个问题")
        return result

