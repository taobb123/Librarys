# 问题采集器系统设计文档

## 设计原则

本系统严格遵循以下设计原则：

1. **接口编程而非类编程**：使用 Python 的 `Protocol` 定义接口，不强制继承
2. **对象组合而非对象继承**：通过组合不同组件实现功能，而不是使用类继承
3. **灵活可扩展**：易于添加新的采集平台和处理器

## 架构设计

### 1. 接口层 (`interfaces.py`)

定义了系统的核心接口：
- `QuestionCollector`: 采集器接口
- `DataProcessor`: 数据处理器接口
- `DuplicateChecker`: 去重检查器接口

使用 `Protocol` 定义，任何实现了这些方法的对象都可以作为对应组件使用。

### 2. 采集器实现 (`collectors/`)

每个社交平台的采集器都是独立的实现：
- `ZhihuCollector`: 知乎采集器
- `WeiboCollector`: 微博采集器

每个采集器通过**组合**以下组件实现功能：
- `HTTPClient`: HTTP 请求客户端
- `RateLimiter`: 速率限制器

### 3. 数据处理器 (`processors.py`)

使用组合模式实现数据处理：
- `QuestionProcessor`: 主处理器，组合多个清洗器和过滤器
- `TextCleaner`: 文本清洗器
- `MinLengthFilter`: 最小长度过滤器
- `ContentQualityFilter`: 内容质量过滤器
- `DatabaseDuplicateChecker`: 数据库去重检查器

### 4. 管理器和服务层

- `CollectorManager`: 采集器管理器，组合多个采集器、处理器和去重检查器
- `CollectionService`: 采集服务，组合管理器和其他业务逻辑

## 使用示例

### 添加新的采集平台

1. 创建新的采集器类，实现 `QuestionCollector` 接口：

```python
class NewPlatformCollector:
    def get_platform_name(self) -> str:
        return "新平台"
    
    def is_available(self) -> bool:
        return True
    
    def collect(self, config: CollectionConfig) -> List[CollectedQuestion]:
        # 实现采集逻辑
        pass
```

2. 在 `service.py` 中注册：

```python
collectors = [
    ZhihuCollector(),
    WeiboCollector(),
    NewPlatformCollector()  # 添加新采集器
]
```

### 添加新的数据处理器

1. 创建处理器类，实现 `DataProcessor` 接口或作为可调用对象：

```python
class CustomFilter:
    def __call__(self, question: CollectedQuestion) -> bool:
        # 实现过滤逻辑
        return True
```

2. 在 `QuestionProcessor` 中使用：

```python
processor = QuestionProcessor(
    filters=[
        MinLengthFilter(),
        ContentQualityFilter(),
        CustomFilter()  # 添加新过滤器
    ]
)
```

## 设计优势

1. **易于扩展**：添加新平台只需实现接口，无需修改现有代码
2. **灵活组合**：可以根据需要组合不同的处理器和过滤器
3. **测试友好**：每个组件都可以独立测试
4. **职责清晰**：每个组件只负责一个功能
5. **符合开闭原则**：对扩展开放，对修改关闭

## 回答采集功能

系统支持在采集问题的同时，自动采集高质量的回答。回答质量通过组合评分器进行评分：

### 回答质量评分器

使用组合模式实现，包含以下评分组件：
- `UpvoteScorer`: 基于点赞数评分（使用对数函数避免高分差过大）
- `ContentLengthScorer`: 基于内容长度评分（接近最优长度时得分更高）
- `RatioScorer`: 基于点赞/点踩比例评分

`DefaultAnswerScorer` 组合以上三个评分器，权重分别为 40%、30%、30%。

### 回答筛选策略

1. 过滤低点赞数回答（可配置最小点赞数）
2. 对每个回答进行质量评分
3. 按质量评分和点赞数排序
4. 每个问题最多保留指定数量的高质量回答

## 第三方API聚合平台

系统支持使用第三方API聚合平台（如聚合数据、ShowAPI等）来获取数据，相比直接调用各平台API，具有更高的稳定性和更宽松的速率限制。

详细配置说明请参考：[第三方API聚合平台使用指南](./README_THIRD_PARTY.md)

### 快速开始

1. **配置环境变量**：
   ```bash
   export USE_THIRD_PARTY_API=true
   export ZHIHU_JUHE_API_KEY=your_juhe_api_key
   export WEIBO_JUHE_API_KEY=your_juhe_api_key
   ```

2. **重启服务**：系统会自动使用第三方API

### 支持的聚合平台

- **聚合数据 (juhe.cn)**：国内知名API聚合平台
  - 微信热搜榜 API：获取微信公众平台热点话题（免费50次/天）
- **ShowAPI**：另一常用API聚合平台
- **自定义平台**：支持配置任意API聚合平台

## 真实API调用

系统已实现真实平台API调用，不再使用模拟数据：

### 知乎采集器
- **API类型**: 公开API，无需认证
- **搜索接口**: `https://www.zhihu.com/api/v4/search_v3`
- **问题详情**: `https://www.zhihu.com/api/v4/questions/{question_id}`
- **回答列表**: `https://www.zhihu.com/api/v4/questions/{question_id}/answers`
- **速率限制**: 0.3 请求/秒（避免触发反爬虫）

### 微信热搜采集器
- **API类型**: 聚合数据第三方API
- **接口地址**: `http://apis.juhe.cn/fapigx/wxhottopic/query`
- **文档**: [聚合数据微信热搜API](https://www.juhe.cn/docs/api/id/737)
- **免费额度**: 50次/天（普通会员）
- **更新频率**: 每10-30分钟更新一次
- **功能**: 获取微信公众平台热点话题榜
- **配置**: 设置 `JUHE_API_KEY` 环境变量
- **特点**: 
  - 返回当前微信热点话题
  - 自动将热搜话题转换为问题格式
  - 如果配置了主题，会优先匹配相关话题

### 微博采集器
- **API类型**: 
  - 优先使用：微博开放平台官方API（需要OAuth 2.0授权）
  - 备用方案：移动端公开接口（无需认证）
- **官方API**:
  - 基础URL: `https://api.weibo.com/2`
  - 微博详情: `statuses/show` ([文档](https://open.weibo.com/wiki/2/statuses/show))
  - 评论列表: `comments/show` ([文档](https://open.weibo.com/wiki/2/comments/show))
  - 用户时间线: `statuses/user_timeline` ([文档](https://open.weibo.com/wiki/2/statuses/user_timeline))
- **移动端API**:
  - 搜索接口: `https://m.weibo.cn/api/container/getIndex`
  - 评论接口: `https://m.weibo.cn/comments/hotflow`
- **速率限制**: 0.2 请求/秒（避免触发反爬虫）
- **配置**: 设置 `WEIBO_APP_KEY`、`WEIBO_APP_SECRET`、`WEIBO_ACCESS_TOKEN` 使用官方API
- **详细文档**: [微博官方API使用指南](./README_WEIBO_API.md)

### 注意事项
1. **速率限制**: 系统已实现速率限制，避免触发平台反爬虫机制
2. **错误处理**: API调用失败时返回空列表，不会降级到模拟数据
3. **HTML清理**: 自动清理API返回的HTML标签，提取纯文本内容
4. **数据质量**: 自动过滤低质量内容（长度、点赞数等）

## API 使用

### 采集问题（含回答）

```bash
POST /api/problems/collect
{
  "topic": "股票",
  "max_results": 50,
  "platform": "知乎",  # 可选
  "auto_save": true,    # 是否自动保存
  "collect_answers": true,  # 是否采集回答
  "max_answers_per_question": 3,  # 每个问题最多采集的回答数
  "min_answer_upvotes": 10  # 回答最小点赞数要求
}
```

### 获取可用平台

```bash
GET /api/problems/collect/platforms
```

### 回答数据模型

回答存储在 `answers` 表中，包含：
- `problem_id`: 关联的问题ID
- `content`: 回答内容
- `author`: 回答作者
- `upvotes`: 点赞数
- `downvotes`: 点踩数
- `quality_score`: 质量评分（0-1）
- `source_url`: 来源链接

