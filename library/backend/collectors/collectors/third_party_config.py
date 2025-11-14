"""
第三方API聚合平台配置
提供常用平台的预设配置
"""
from typing import Dict, List


# 预设的第三方API配置
THIRD_PARTY_CONFIGS = {
    'zhihu_juhe': {
        'provider': 'juhe',
        'base_url': 'http://v.juhe.cn',
        'search_endpoint': 'zhihu/search',
        'params_mapping': {
            'topic': 'q',
            'max_results': 'pagesize'
        },
        'response_mapping': {
            'items_path': 'result.data',
            'fields': {
                'title': 'title',
                'content': 'excerpt',
                'source_url': 'url',
                'author': 'author.name',
                'created_at': 'created_time'
            },
            'answers_field': 'answers',
            'answer_fields': {
                'content': 'content',
                'author': 'author.name',
                'upvotes': 'voteup_count',
                'downvotes': 'votedown_count',
                'source_url': 'url'
            }
        }
    },
    
    'weibo_juhe': {
        'provider': 'juhe',
        'base_url': 'http://v.juhe.cn',
        'search_endpoint': 'weibo/search',
        'params_mapping': {
            'topic': 'q',
            'max_results': 'pagesize'
        },
        'response_mapping': {
            'items_path': 'result.data',
            'fields': {
                'title': 'text',
                'content': 'text',
                'source_url': 'url',
                'author': 'user.screen_name',
                'created_at': 'created_at'
            },
            'answers_field': 'comments',
            'answer_fields': {
                'content': 'text',
                'author': 'user.screen_name',
                'upvotes': 'like_count',
                'source_url': 'url'
            }
        }
    },
    
    'zhihu_showapi': {
        'provider': 'showapi',
        'base_url': 'https://route.showapi.com',
        'search_endpoint': 'xxx-xxx',  # 需要替换为实际的ShowAPI接口编号
        'params_mapping': {
            'topic': 'keyword',
            'max_results': 'pageSize'
        },
        'response_mapping': {
            'items_path': 'showapi_res_body.list',
            'fields': {
                'title': 'title',
                'content': 'content',
                'source_url': 'url',
                'author': 'author',
                'created_at': 'created'
            }
        }
    }
}


def get_third_party_config(platform: str, provider: str = 'juhe') -> Dict:
    """获取第三方API配置
    
    Args:
        platform: 平台名称（'zhihu' 或 'weibo'）
        provider: 提供商（'juhe', 'showapi'等）
        
    Returns:
        配置字典
    """
    config_key = f'{platform}_{provider}'
    return THIRD_PARTY_CONFIGS.get(config_key, {})


def list_available_providers() -> List[str]:
    """列出可用的API提供商"""
    return ['juhe', 'showapi', 'custom']


def list_available_platforms() -> List[str]:
    """列出支持的平台"""
    return ['zhihu', 'weibo']






