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

## API 使用

### 采集问题

```bash
POST /api/problems/collect
{
  "topic": "股票",
  "max_results": 50,
  "platform": "知乎",  # 可选
  "auto_save": true    # 是否自动保存
}
```

### 获取可用平台

```bash
GET /api/problems/collect/platforms
```

