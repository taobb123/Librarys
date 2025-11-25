"""
回答质量评分器实现
使用组合模式，可以灵活组合不同的评分策略
"""
from typing import List
from backend.collectors.interfaces import CollectedAnswer, AnswerQualityScorer


class UpvoteScorer:
    """基于点赞数的评分器组件"""
    
    def __init__(self, min_upvotes: int = 10, max_upvotes: int = 10000):
        self.min_upvotes = min_upvotes
        self.max_upvotes = max_upvotes
    
    def score(self, answer: CollectedAnswer) -> float:
        """基于点赞数计算评分"""
        upvotes = answer.upvotes
        if upvotes < self.min_upvotes:
            return 0.0
        
        # 使用对数函数，避免高分差过大
        import math
        normalized = min(upvotes / self.max_upvotes, 1.0)
        return math.log(1 + normalized * 9) / math.log(10)  # 0-1之间的对数评分


class ContentLengthScorer:
    """基于内容长度的评分器组件"""
    
    def __init__(self, min_length: int = 50, optimal_length: int = 500):
        self.min_length = min_length
        self.optimal_length = optimal_length
    
    def score(self, answer: CollectedAnswer) -> float:
        """基于内容长度计算评分"""
        length = len(answer.content)
        if length < self.min_length:
            return 0.0
        
        # 接近最优长度时得分更高
        if length <= self.optimal_length:
            return min(length / self.optimal_length, 1.0)
        else:
            # 过长也会适当降分
            return max(0.5, 1.0 - (length - self.optimal_length) / (self.optimal_length * 2))


class RatioScorer:
    """基于点赞/点踩比例的评分器组件"""
    
    def score(self, answer: CollectedAnswer) -> float:
        """基于点赞点踩比例计算评分"""
        upvotes = answer.upvotes
        downvotes = answer.downvotes
        
        if upvotes + downvotes == 0:
            return 0.5  # 没有投票，中性评分
        
        ratio = upvotes / (upvotes + downvotes)
        return ratio


class CompositeAnswerScorer:
    """组合评分器
    
    使用组合模式，组合多个评分器组件
    """
    
    def __init__(self, scorers: List[AnswerQualityScorer] = None, weights: List[float] = None):
        """
        初始化组合评分器
        
        Args:
            scorers: 评分器列表
            weights: 权重列表，长度应与scorers相同
        """
        self.scorers = scorers or []
        self.weights = weights or [1.0] * len(self.scorers)
        
        # 归一化权重
        total_weight = sum(self.weights)
        if total_weight > 0:
            self.weights = [w / total_weight for w in self.weights]
    
    def score(self, answer: CollectedAnswer) -> float:
        """计算综合评分"""
        if not self.scorers:
            return 0.5  # 默认评分
        
        scores = []
        for scorer in self.scorers:
            try:
                score = scorer.score(answer)
                scores.append(score)
            except Exception:
                scores.append(0.0)
        
        # 加权平均
        weighted_sum = sum(score * weight for score, weight in zip(scores, self.weights))
        return weighted_sum


class DefaultAnswerScorer:
    """默认回答评分器
    
    组合点赞数、内容长度和点赞比例评分器
    """
    
    def __init__(self, min_upvotes: int = 10):
        """初始化默认评分器"""
        upvote_scorer = UpvoteScorer(min_upvotes=min_upvotes)
        length_scorer = ContentLengthScorer()
        ratio_scorer = RatioScorer()
        
        # 组合评分器，设置权重：点赞数40%，内容长度30%，点赞比例30%
        self.composite = CompositeAnswerScorer(
            scorers=[upvote_scorer, length_scorer, ratio_scorer],
            weights=[0.4, 0.3, 0.3]
        )
    
    def score(self, answer: CollectedAnswer) -> float:
        """计算回答质量评分"""
        return self.composite.score(answer)







