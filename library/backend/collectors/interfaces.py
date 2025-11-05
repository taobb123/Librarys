"""
采集器接口定义
使用Protocol定义接口，遵循接口编程而非类编程的原则
"""
from typing import Protocol, List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CollectedQuestion:
    """采集的问题数据结构"""
    title: str
    content: str
    source: str  # 来源平台
    source_url: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CollectionConfig:
    """采集配置"""
    topic: str  # 主题，如"股票"
    max_results: int = 50  # 最大采集数量
    platform: Optional[str] = None  # 指定平台，None表示所有平台
    filters: Dict[str, Any] = None  # 额外的过滤条件
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


class QuestionCollector(Protocol):
    """问题采集器接口
    
    使用Protocol定义接口，不强制继承，任何实现了这些方法的对象都可以作为采集器
    """
    
    def get_platform_name(self) -> str:
        """获取平台名称"""
        ...
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        """采集问题
        
        Args:
            config: 采集配置
            
        Returns:
            采集到的问题列表
        """
        ...
    
    def is_available(self) -> bool:
        """检查采集器是否可用（如API是否配置等）"""
        ...


class DataProcessor(Protocol):
    """数据处理器接口
    
    用于数据清洗、转换、过滤等处理
    """
    
    def process(self, questions: List[CollectedQuestion]) -> List[CollectedQuestion]:
        """处理问题列表"""
        ...


class DuplicateChecker(Protocol):
    """去重检查器接口"""
    
    def is_duplicate(self, question: CollectedQuestion) -> bool:
        """检查问题是否重复"""
        ...
    
    def mark_as_seen(self, question: CollectedQuestion) -> None:
        """标记问题为已处理"""
        ...

