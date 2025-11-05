"""
数据处理器实现
使用组合模式，可以灵活组合不同的处理功能
"""
from typing import List
from backend.collectors.interfaces import CollectedQuestion, DataProcessor, DuplicateChecker
import re
from datetime import datetime


class TextCleaner:
    """文本清洗器"""
    
    def clean(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊控制字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 移除HTML标签（如果存在）
        text = re.sub(r'<[^>]+>', '', text)
        
        return text.strip()


class QuestionProcessor:
    """问题处理器（组合多个处理功能）"""
    
    def __init__(self, cleaners: List[DataProcessor] = None, filters: List = None):
        """使用组合模式，可以灵活添加不同的处理器"""
        self.cleaners = cleaners or []
        self.filters = filters or []
        self.text_cleaner = TextCleaner()
    
    def process(self, questions: List[CollectedQuestion]) -> List[CollectedQuestion]:
        """处理问题列表"""
        processed = []
        
        for question in questions:
            # 清洗文本
            question.title = self.text_cleaner.clean(question.title)
            question.content = self.text_cleaner.clean(question.content)
            
            # 应用其他清洗器
            for cleaner in self.cleaners:
                question = cleaner.process([question])[0] if hasattr(cleaner, 'process') else question
            
            # 应用过滤器
            if self._should_include(question):
                processed.append(question)
        
        return processed
    
    def _should_include(self, question: CollectedQuestion) -> bool:
        """判断是否应该包含该问题"""
        for filter_func in self.filters:
            if callable(filter_func) and not filter_func(question):
                return False
        return True


class MinLengthFilter:
    """最小长度过滤器"""
    
    def __init__(self, min_title_length: int = 5, min_content_length: int = 10):
        self.min_title_length = min_title_length
        self.min_content_length = min_content_length
    
    def __call__(self, question: CollectedQuestion) -> bool:
        """判断问题是否符合最小长度要求"""
        return (len(question.title) >= self.min_title_length and 
                len(question.content) >= self.min_content_length)


class ContentQualityFilter:
    """内容质量过滤器"""
    
    def __call__(self, question: CollectedQuestion) -> bool:
        """过滤低质量问题"""
        # 检查是否包含问号或疑问词
        question_words = ['什么', '如何', '为什么', '怎么', '哪些', '哪个', '?', '？', '吗']
        has_question = any(word in question.title or word in question.content 
                          for word in question_words)
        
        # 检查是否过于简短
        is_too_short = len(question.title) < 3 or len(question.content) < 5
        
        # 检查是否包含过多特殊字符
        special_char_ratio = sum(1 for c in question.title if not c.isalnum() and c not in '，。！？、') / max(len(question.title), 1)
        has_too_many_special = special_char_ratio > 0.5
        
        return has_question and not is_too_short and not has_too_many_special


class DatabaseDuplicateChecker:
    """基于数据库的去重检查器"""
    
    def __init__(self, problem_model_module):
        """通过组合problem_model来实现去重"""
        self.problem_model = problem_model_module
        self._seen_titles = set()
    
    def is_duplicate(self, question: CollectedQuestion) -> bool:
        """检查问题是否重复"""
        # 检查内存中的缓存
        title_normalized = self._normalize_title(question.title)
        if title_normalized in self._seen_titles:
            return True
        
        # 检查数据库中的重复
        try:
            all_problems = self.problem_model.get_all_problems()
            for problem in all_problems:
                if self._normalize_title(problem.get('title', '')) == title_normalized:
                    return True
        except Exception:
            # 如果数据库查询失败，只使用内存缓存
            pass
        
        return False
    
    def mark_as_seen(self, question: CollectedQuestion) -> None:
        """标记问题为已处理"""
        title_normalized = self._normalize_title(question.title)
        self._seen_titles.add(title_normalized)
    
    def _normalize_title(self, title: str) -> str:
        """标准化标题用于比较"""
        if not title:
            return ""
        # 移除标点符号和空白，转为小写
        normalized = re.sub(r'[^\w]', '', title.lower())
        return normalized

