"""
检查配置
用于验证API密钥等配置是否正确
"""
import os
from backend.config import Config

def check_env_config():
    """检查配置"""
    print("=" * 50)
    print("配置检查")
    print("=" * 50)
    
    # 检查聚合数据API密钥（从配置文件读取）
    juhe_key = Config.JUHE_API_KEY
    if juhe_key:
        print(f"✅ JUHE_API_KEY: 已配置 ({juhe_key[:10]}...)")
        print(f"   配置文件: backend/config.py")
    else:
        print("❌ JUHE_API_KEY: 未配置（请在backend/config.py中配置）")
    
    # 检查第三方API配置
    use_third_party = os.getenv('USE_THIRD_PARTY_API', 'false').lower() == 'true'
    if use_third_party:
        print("✅ USE_THIRD_PARTY_API: 已启用")
    else:
        print("ℹ️  USE_THIRD_PARTY_API: 未启用（使用直接API）")
    
    # 检查微博配置
    weibo_app_key = os.getenv('WEIBO_APP_KEY', '')
    weibo_access_token = os.getenv('WEIBO_ACCESS_TOKEN', '')
    if weibo_app_key:
        print(f"✅ WEIBO_APP_KEY: 已配置")
    else:
        print("ℹ️  WEIBO_APP_KEY: 未配置（使用移动端API）")
    
    if weibo_access_token:
        print(f"✅ WEIBO_ACCESS_TOKEN: 已配置")
    else:
        print("ℹ️  WEIBO_ACCESS_TOKEN: 未配置（使用移动端API）")
    
    print("=" * 50)
    
    # 测试采集器可用性
    print("\n采集器可用性检查：")
    print("-" * 50)
    
    try:
        from backend.collectors.collectors.weixin_hot_collector import WeixinHotCollector
        weixin_collector = WeixinHotCollector()
        if weixin_collector.is_available():
            print("✅ 微信热搜采集器: 可用")
        else:
            print("❌ 微信热搜采集器: 不可用（请在backend/config.py中配置JUHE_API_KEY）")
    except Exception as e:
        print(f"❌ 微信热搜采集器: 检查失败 - {str(e)}")
    
    try:
        from backend.collectors.collectors.zhihu_collector import ZhihuCollector
        zhihu_collector = ZhihuCollector()
        if zhihu_collector.is_available():
            print("✅ 知乎采集器: 可用")
        else:
            print("❌ 知乎采集器: 不可用")
    except Exception as e:
        print(f"❌ 知乎采集器: 检查失败 - {str(e)}")
    
    try:
        from backend.collectors.collectors.weibo_collector import WeiboCollector
        weibo_collector = WeiboCollector()
        if weibo_collector.is_available():
            print("✅ 微博采集器: 可用")
        else:
            print("❌ 微博采集器: 不可用")
    except Exception as e:
        print(f"❌ 微博采集器: 检查失败 - {str(e)}")
    
    print("=" * 50)

if __name__ == '__main__':
    check_env_config()

