"""
基础采集器组件
使用组合模式而非继承
"""
from typing import List, Optional
from backend.collectors.interfaces import CollectedQuestion, CollectionConfig
import requests
import time


class HTTPClient:
    """HTTP客户端组件（可组合使用）"""
    
    def __init__(self, timeout: int = 30, headers: dict = None):
        self.timeout = timeout
        self.default_headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get(self, url: str, params: dict = None, headers: dict = None) -> requests.Response:
        """发送GET请求"""
        merged_headers = {**self.default_headers, **(headers or {})}
        return requests.get(url, params=params, headers=merged_headers, timeout=self.timeout)
    
    def post(self, url: str, data: dict = None, json: dict = None, headers: dict = None) -> requests.Response:
        """发送POST请求"""
        merged_headers = {**self.default_headers, **(headers or {})}
        return requests.post(url, data=data, json=json, headers=merged_headers, timeout=self.timeout)


class RateLimiter:
    """速率限制器组件"""
    
    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
    
    def wait_if_needed(self) -> None:
        """如果需要，等待一段时间"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        
        self.last_request_time = time.time()

