"""
平台API可用性测试工具
用于测试各个采集平台的API连接和响应
"""
from typing import Dict, List
import requests
import time
from datetime import datetime


def test_api_endpoint(url: str, params: dict = None, headers: dict = None, timeout: int = 10) -> Dict:
    """测试单个API端点
    
    Args:
        url: API地址
        params: 请求参数
        headers: 请求头
        timeout: 超时时间（秒）
        
    Returns:
        测试结果字典
    """
    result = {
        'url': url,
        'accessible': False,
        'status_code': None,
        'response_time': None,
        'error': None,
        'response_size': None,
        'has_data': False
    }
    
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    if headers:
        default_headers.update(headers)
    
    start_time = time.time()
    
    try:
        response = requests.get(url, params=params, headers=default_headers, timeout=timeout)
        elapsed_time = time.time() - start_time
        
        result['status_code'] = response.status_code
        result['response_time'] = round(elapsed_time * 1000, 2)  # 转换为毫秒
        result['response_size'] = len(response.content)
        result['accessible'] = response.status_code == 200
        
        # 尝试解析JSON，检查是否有数据
        try:
            data = response.json()
            if isinstance(data, dict):
                result['has_data'] = bool(data.get('data')) or bool(data.get('data'))
            elif isinstance(data, list):
                result['has_data'] = len(data) > 0
        except:
            pass
            
    except requests.exceptions.Timeout:
        result['error'] = f'请求超时（{timeout}秒）'
    except requests.exceptions.ConnectionError:
        result['error'] = '连接失败（无法连接到服务器）'
    except requests.exceptions.RequestException as e:
        result['error'] = f'请求异常: {str(e)}'
    except Exception as e:
        result['error'] = f'未知错误: {str(e)}'
    
    return result


def test_zhihu_api() -> Dict:
    """测试知乎API可用性"""
    results = {
        'platform': '知乎',
        'overall_status': 'unknown',
        'endpoints': {},
        'summary': {
            'total': 0,
            'accessible': 0,
            'failed': 0
        }
    }
    
    # 测试搜索API
    search_url = 'https://www.zhihu.com/api/v4/search_v3'
    search_params = {
        'q': '股票',
        't': 'general',
        'limit': 5,
        'offset': 0
    }
    
    print(f"[API测试] 测试知乎搜索API: {search_url}")
    search_result = test_api_endpoint(search_url, params=search_params, headers={
        'Referer': 'https://www.zhihu.com/'
    })
    results['endpoints']['search'] = search_result
    results['summary']['total'] += 1
    if search_result['accessible']:
        results['summary']['accessible'] += 1
    else:
        results['summary']['failed'] += 1
    
    # 测试问题详情API（使用一个示例问题ID）
    # 注意：这里使用一个可能存在的问题ID，实际测试时可能失败，但不影响整体判断
    question_url = 'https://www.zhihu.com/api/v4/questions/19550225'  # 示例问题ID
    print(f"[API测试] 测试知乎问题API: {question_url}")
    question_result = test_api_endpoint(question_url)
    results['endpoints']['question_detail'] = question_result
    results['summary']['total'] += 1
    if question_result['accessible']:
        results['summary']['accessible'] += 1
    else:
        results['summary']['failed'] += 1
    
    # 判断整体状态
    if results['summary']['accessible'] == results['summary']['total']:
        results['overall_status'] = 'available'
    elif results['summary']['accessible'] > 0:
        results['overall_status'] = 'partial'
    else:
        results['overall_status'] = 'unavailable'
    
    return results


def test_weibo_api() -> Dict:
    """测试微博API可用性"""
    results = {
        'platform': '微博',
        'overall_status': 'unknown',
        'endpoints': {},
        'summary': {
            'total': 0,
            'accessible': 0,
            'failed': 0
        }
    }
    
    # 测试搜索API
    search_url = 'https://m.weibo.cn/api/container/getIndex'
    search_params = {
        'containerid': '100103type=1&q=股票',
        'page_type': 'searchall',
        'page': 1
    }
    
    print(f"[API测试] 测试微博搜索API: {search_url}")
    search_result = test_api_endpoint(search_url, params=search_params, headers={
        'Referer': 'https://weibo.com/'
    })
    results['endpoints']['search'] = search_result
    results['summary']['total'] += 1
    if search_result['accessible']:
        results['summary']['accessible'] += 1
    else:
        results['summary']['failed'] += 1
    
    # 判断整体状态
    if results['summary']['accessible'] == results['summary']['total']:
        results['overall_status'] = 'available'
    elif results['summary']['accessible'] > 0:
        results['overall_status'] = 'partial'
    else:
        results['overall_status'] = 'unavailable'
    
    return results


def test_weixin_hot_api() -> Dict:
    """测试微信热搜API可用性（聚合数据）"""
    results = {
        'platform': '微信热搜',
        'overall_status': 'unknown',
        'endpoints': {},
        'summary': {
            'total': 0,
            'accessible': 0,
            'failed': 0
        }
    }
    
    # 测试微信热搜API（聚合数据）
    api_url = 'http://apis.juhe.cn/fapigx/wxhottopic/query'
    from backend.config import Config
    api_key = Config.JUHE_API_KEY
    
    if not api_key:
        results['summary']['total'] = 1
        results['summary']['failed'] = 1
        results['overall_status'] = 'unavailable'
        results['endpoints']['search'] = {
            'url': api_url,
            'accessible': False,
            'error': '未配置JUHE_API_KEY（请在backend/config.py中配置）'
        }
        return results
    
    print(f"[API测试] 测试微信热搜API: {api_url}")
    search_result = test_api_endpoint(api_url, params={'key': api_key})
    results['endpoints']['search'] = search_result
    results['summary']['total'] += 1
    
    if search_result['accessible']:
        results['summary']['accessible'] += 1
        # 检查返回数据格式
        if search_result.get('has_data'):
            results['overall_status'] = 'available'
        else:
            results['overall_status'] = 'partial'
    else:
        results['summary']['failed'] += 1
        results['overall_status'] = 'unavailable'
    
    return results


def test_all_platforms() -> Dict:
    """测试所有平台的API可用性"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'platforms': {},
        'summary': {
            'total_platforms': 0,
            'available_platforms': 0,
            'partial_platforms': 0,
            'unavailable_platforms': 0
        }
    }
    
    print("[API测试] 开始测试所有平台API可用性...")
    
    # 测试知乎
    print("\n[API测试] ========== 测试知乎API ==========")
    zhihu_result = test_zhihu_api()
    results['platforms']['知乎'] = zhihu_result
    results['summary']['total_platforms'] += 1
    if zhihu_result['overall_status'] == 'available':
        results['summary']['available_platforms'] += 1
    elif zhihu_result['overall_status'] == 'partial':
        results['summary']['partial_platforms'] += 1
    else:
        results['summary']['unavailable_platforms'] += 1
    
    # 稍作延迟，避免请求过快
    time.sleep(1)
    
    # 测试微博
    print("\n[API测试] ========== 测试微博API ==========")
    weibo_result = test_weibo_api()
    results['platforms']['微博'] = weibo_result
    results['summary']['total_platforms'] += 1
    if weibo_result['overall_status'] == 'available':
        results['summary']['available_platforms'] += 1
    elif weibo_result['overall_status'] == 'partial':
        results['summary']['partial_platforms'] += 1
    else:
        results['summary']['unavailable_platforms'] += 1
    
    # 稍作延迟
    time.sleep(1)
    
    # 测试微信热搜
    print("\n[API测试] ========== 测试微信热搜API ==========")
    weixin_result = test_weixin_hot_api()
    results['platforms']['微信热搜'] = weixin_result
    results['summary']['total_platforms'] += 1
    if weixin_result['overall_status'] == 'available':
        results['summary']['available_platforms'] += 1
    elif weixin_result['overall_status'] == 'partial':
        results['summary']['partial_platforms'] += 1
    else:
        results['summary']['unavailable_platforms'] += 1
    
    print("\n[API测试] ========== 测试完成 ==========")
    print(f"[API测试] 总平台数: {results['summary']['total_platforms']}")
    print(f"[API测试] 可用平台: {results['summary']['available_platforms']}")
    print(f"[API测试] 部分可用: {results['summary']['partial_platforms']}")
    print(f"[API测试] 不可用平台: {results['summary']['unavailable_platforms']}")
    
    return results

