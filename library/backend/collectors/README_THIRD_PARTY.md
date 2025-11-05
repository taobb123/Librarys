# 第三方API聚合平台使用指南

## 概述

系统支持使用第三方API聚合平台来获取数据，相比直接调用各平台API，具有以下优势：

1. **稳定性更高**：聚合平台通常有更好的反爬虫处理
2. **统一接口**：不同平台使用相同的接口格式
3. **数据质量**：聚合平台通常会对数据进行清洗和格式化
4. **速率限制更宽松**：相比直接调用，限制更少

## 支持的聚合平台

### 1. 聚合数据 (juhe.cn)

聚合数据是国内知名的API聚合平台，提供多种数据接口。

**注册和获取API Key：**
1. 访问 [聚合数据官网](https://www.juhe.cn/)
2. 注册账号
3. 在控制台中找到需要的API
4. 申请API Key（可在个人中心查看）

**支持的API：**

#### 微信热搜榜 API
- **接口ID**: 737
- **接口地址**: `http://apis.juhe.cn/fapigx/wxhottopic/query`
- **文档**: https://www.juhe.cn/docs/api/id/737
- **免费额度**: 50次/天（普通会员）
- **功能**: 获取微信公众平台热点话题榜，每10-30分钟更新一次

**配置方式：**
```bash
# 设置聚合数据API密钥（通用）
export JUHE_API_KEY=your_juhe_api_key

# 或者针对特定平台
export ZHIHU_JUHE_API_KEY=your_juhe_api_key
export WEIBO_JUHE_API_KEY=your_juhe_api_key

# 启用第三方API（可选）
export USE_THIRD_PARTY_API=true
```

**微信热搜API使用：**
- 只需配置 `JUHE_API_KEY`，系统会自动启用微信热搜采集器
- 微信热搜API返回热点话题，系统会自动转换为问题格式
- 热搜话题会作为问题标题，内容包含话题描述和排名信息
- 如果采集时输入了主题，系统会优先返回包含该主题的热搜话题
- **注意**: 微信热搜API不提供回答数据，只采集话题本身

**示例：**
```bash
# 配置API密钥
export JUHE_API_KEY=your_juhe_api_key

# 重启后端服务
# 系统会自动检测并启用微信热搜采集器
```

**API返回格式：**
```json
{
  "error_code": 0,
  "reason": "success",
  "result": {
    "list": [
      {
        "word": "助力上合组织国家农业现代化",
        "index": 9
      },
      {
        "word": "中国城市人口密度榜出炉",
        "index": 8
      }
    ]
  }
}
```

**系统转换：**
- 热搜话题 "助力上合组织国家农业现代化" 
- 转换为问题标题: "关于助力上合组织国家农业现代化的讨论"
- 问题内容: "微信热搜话题：助力上合组织国家农业现代化。这是当前微信公众平台的热点话题，排名第10位。"

### 2. ShowAPI

ShowAPI是另一个常用的API聚合平台。

**配置方式：**
```bash
export SHOWAPI_APPID=your_app_id
export SHOWAPI_SECRET=your_secret
export USE_THIRD_PARTY_API=true
```

### 3. 自定义API平台

系统支持自定义API聚合平台，只需提供相应的配置。

## 配置说明

### 环境变量配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `USE_THIRD_PARTY_API` | 是否使用第三方API | `true` 或 `false` |
| `ZHIHU_JUHE_API_KEY` | 知乎聚合数据API密钥 | `your_key_here` |
| `WEIBO_JUHE_API_KEY` | 微博聚合数据API密钥 | `your_key_here` |
| `SHOWAPI_APPID` | ShowAPI应用ID | `your_app_id` |
| `SHOWAPI_SECRET` | ShowAPI密钥 | `your_secret` |

### 自定义配置

如果需要使用其他聚合平台或自定义配置，可以在代码中创建采集器：

```python
from backend.collectors.collectors.third_party_collector import create_custom_collector

config = {
    'base_url': 'https://api.example.com',
    'api_key': 'your_api_key',
    'search_endpoint': 'search',
    'params_mapping': {
        'topic': 'keyword',
        'max_results': 'limit'
    },
    'response_mapping': {
        'items_path': 'data.results',
        'fields': {
            'title': 'title',
            'content': 'content',
            'source_url': 'url'
        }
    }
}

collector = create_custom_collector('平台名称', config)
```

## 响应映射配置

响应映射用于将第三方API的响应格式转换为系统内部格式。

### 字段映射

```python
'fields': {
    'title': 'title',           # 标题字段路径
    'content': 'content',       # 内容字段路径
    'source_url': 'url',        # 链接字段路径
    'author': 'author.name',    # 作者字段路径（支持点号分隔）
    'created_at': 'created_time' # 创建时间字段路径
}
```

### 回答字段映射

```python
'answer_fields': {
    'content': 'content',
    'author': 'author.name',
    'upvotes': 'voteup_count',
    'downvotes': 'votedown_count',
    'source_url': 'url'
}
```

### 数据项路径

```python
'items_path': 'result.data'  # API响应中数据列表的路径，支持点号分隔
```

## 使用示例

### 1. 使用聚合数据平台

```bash
# 设置环境变量
export USE_THIRD_PARTY_API=true
export ZHIHU_JUHE_API_KEY=your_juhe_key

# 启动后端服务
python backend/app.py
```

### 2. 在代码中使用

```python
from backend.collectors.collectors.third_party_collector import create_juhe_collector
from backend.collectors.interfaces import CollectionConfig

# 创建采集器
collector = create_juhe_collector(
    '知乎',
    api_key='your_juhe_key',
    api_config={
        'search_endpoint': 'zhihu/search',
        'response_mapping': {...}
    }
)

# 采集数据
config = CollectionConfig(
    topic='股票',
    max_results=10,
    collect_answers=True
)
questions = collector.collect(config)
```

## 优势对比

### 直接API vs 第三方API

| 特性 | 直接API | 第三方API |
|------|---------|-----------|
| 稳定性 | 可能被反爬虫 | 更稳定 |
| 速率限制 | 较严格 | 较宽松 |
| 配置复杂度 | 简单 | 需要API Key |
| 成本 | 免费 | 可能需要付费 |
| 数据质量 | 原始数据 | 通常已清洗 |

## 注意事项

1. **API配额**：第三方API平台通常有调用次数限制，注意配额使用
2. **费用**：部分平台可能收费，请查看平台定价
3. **响应格式**：不同平台的响应格式不同，需要正确配置映射
4. **降级策略**：如果第三方API失败，可以回退到直接API

## 故障排查

### API Key无效

检查环境变量是否正确设置：
```bash
echo $ZHIHU_JUHE_API_KEY
```

### 响应格式不匹配

检查响应映射配置是否正确，可以打印API响应查看实际格式：
```python
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

### 请求失败

检查网络连接和API端点URL是否正确。

## 更多信息

- [聚合数据文档](https://www.juhe.cn/docs)
- [ShowAPI文档](https://www.showapi.com/api/viewList)
- 系统采集器代码：`backend/collectors/collectors/third_party_collector.py`

