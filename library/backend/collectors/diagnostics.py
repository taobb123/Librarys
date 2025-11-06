"""
采集系统诊断工具
用于检查采集系统的状态和可用性
"""
from typing import List, Dict
from backend.collectors.collector_manager import CollectorManager
from backend.collectors.interfaces import CollectionConfig
from backend.collectors.collectors.zhihu_collector import ZhihuCollector
from backend.collectors.collectors.weibo_collector import WeiboCollector


def diagnose_collectors() -> Dict:
    """诊断采集器系统
    
    Returns:
        包含诊断信息的字典
    """
    result = {
        'collectors': {},
        'summary': {
            'total': 0,
            'available': 0,
            'unavailable': 0
        }
    }
    
    # 创建测试采集器
    collectors = [
        ZhihuCollector(),
        WeiboCollector()
    ]
    
    for collector in collectors:
        platform_name = collector.get_platform_name()
        is_available = collector.is_available()
        
        # 测试采集（使用最小配置）
        test_config = CollectionConfig(
            topic='测试',
            max_results=1,
            collect_answers=False
        )
        
        test_result = None
        test_error = None
        try:
            test_questions = collector.collect(test_config)
            test_result = {
                'success': True,
                'count': len(test_questions),
                'sample': test_questions[0].title if test_questions else None
            }
        except Exception as e:
            test_result = {
                'success': False,
                'error': str(e)
            }
            test_error = str(e)
        
        result['collectors'][platform_name] = {
            'name': platform_name,
            'available': is_available,
            'test_result': test_result,
            'error': test_error
        }
        
        result['summary']['total'] += 1
        if is_available:
            result['summary']['available'] += 1
        else:
            result['summary']['unavailable'] += 1
    
    return result


def check_collection_flow(config: CollectionConfig) -> Dict:
    """检查采集流程
    
    Args:
        config: 采集配置
        
    Returns:
        包含各阶段数据的字典
    """
    from backend.collectors.processors import (
        QuestionProcessor, MinLengthFilter, ContentQualityFilter
    )
    from backend.collectors.processors import DatabaseDuplicateChecker
    import backend.models.problem_model as problem_model
    
    result = {
        'stages': {},
        'errors': []
    }
    
    try:
        # 1. 检查采集器
        collectors = [ZhihuCollector(), WeiboCollector()]
        manager = CollectorManager(collectors=collectors)
        
        available = manager.get_available_collectors()
        result['stages']['collectors'] = {
            'total': len(collectors),
            'available': len(available),
            'platforms': available
        }
        
        # 2. 执行采集
        raw_questions = manager.collect(config)
        result['stages']['raw_collection'] = {
            'count': len(raw_questions),
            'titles': [q.title for q in raw_questions[:3]]
        }
        
        # 3. 测试处理器
        processor = QuestionProcessor(
            filters=[
                MinLengthFilter(min_title_length=5, min_content_length=10),
                ContentQualityFilter()
            ]
        )
        processed = processor.process(raw_questions)
        result['stages']['processed'] = {
            'count': len(processed),
            'filtered': len(raw_questions) - len(processed)
        }
        
        # 4. 测试去重
        duplicate_checker = DatabaseDuplicateChecker(problem_model)
        unique = []
        duplicates = 0
        for q in processed:
            if not duplicate_checker.is_duplicate(q):
                unique.append(q)
                duplicate_checker.mark_as_seen(q)
            else:
                duplicates += 1
        
        result['stages']['deduplicated'] = {
            'count': len(unique),
            'duplicates': duplicates
        }
        
    except Exception as e:
        import traceback
        result['errors'].append({
            'stage': 'unknown',
            'error': str(e),
            'traceback': traceback.format_exc()
        })
    
    return result



