# 微博开放平台API使用指南

## 概述

系统已支持使用微博开放平台官方API来获取数据。参考文档：[微博API文档](https://open.weibo.com/wiki/微博API)

## 配置步骤

### 1. 注册微博开放平台账号

1. 访问 [微博开放平台](https://open.weibo.com/)
2. 使用微博账号登录
3. 在"管理中心"创建新应用
4. 填写应用信息并提交审核

### 2. 获取App Key和App Secret

应用审核通过后，在应用详情页可以找到：
- **App Key**: 应用唯一标识
- **App Secret**: 应用密钥

### 3. OAuth 2.0授权

微博API采用OAuth 2.0授权机制，需要获取access_token：

#### 授权流程

1. **构造授权URL**：
   ```
   https://api.weibo.com/oauth2/authorize?client_id=YOUR_APP_KEY&redirect_uri=YOUR_REDIRECT_URI&response_type=code
   ```

2. **用户授权**：用户在浏览器中访问授权URL并同意授权

3. **获取授权码**：授权后，微博会重定向到回调地址，URL中包含授权码（code）

4. **换取access_token**：
   ```
   POST https://api.weibo.com/oauth2/access_token
   {
     "client_id": "YOUR_APP_KEY",
     "client_secret": "YOUR_APP_SECRET",
     "grant_type": "authorization_code",
     "code": "授权码",
     "redirect_uri": "YOUR_REDIRECT_URI"
   }
   ```

### 4. 配置环境变量

```bash
# 微博开放平台配置
export WEIBO_APP_KEY=your_app_key
export WEIBO_APP_SECRET=your_app_secret
export WEIBO_ACCESS_TOKEN=your_access_token
```

## 支持的API接口

### 1. 获取微博信息

- **接口**: `statuses/show`
- **文档**: https://open.weibo.com/wiki/2/statuses/show
- **功能**: 根据微博ID获取单条微博信息
- **参数**: `access_token`, `id`

### 2. 获取用户时间线

- **接口**: `statuses/user_timeline`
- **文档**: https://open.weibo.com/wiki/2/statuses/user_timeline
- **功能**: 获取授权用户发布的微博
- **参数**: `access_token`, `uid`或`screen_name`

### 3. 获取评论列表

- **接口**: `comments/show`
- **文档**: https://open.weibo.com/wiki/2/comments/show
- **功能**: 获取某条微博的评论列表
- **参数**: `access_token`, `id`, `count`, `page`

## 系统实现

### 智能降级策略

系统实现了智能降级策略：

1. **优先使用官方API**：如果配置了`WEIBO_ACCESS_TOKEN`，优先使用微博开放平台官方API
2. **自动降级**：如果官方API失败或未配置，自动降级到移动端API（公开接口）

### 评论采集

- **有access_token**：使用`comments/show`接口获取评论（更稳定、数据更完整）
- **无access_token**：使用移动端API获取评论（作为备用方案）

## 注意事项

### 1. API限制

- **访问频率限制**：微博API有访问频率限制，系统已实现速率限制（0.2请求/秒）
- **权限限制**：部分接口需要高级权限，需要单独申请
- **Scope限制**：部分接口需要用户单独授权特定的Scope

### 2. 搜索功能

微博开放平台的标准API主要用于获取授权用户的数据，对于公开关键词搜索，可能需要：
- 使用商业接口（需要申请）
- 使用移动端API（当前实现）
- 使用第三方API聚合平台

### 3. access_token有效期

- access_token通常有有效期限制
- 过期后需要重新授权获取新的access_token
- 可以使用refresh_token刷新access_token（如果支持）

## 使用示例

### 配置环境变量

```bash
export WEIBO_APP_KEY=1234567890
export WEIBO_APP_SECRET=abcdefghijklmnopqrstuvwxyz
export WEIBO_ACCESS_TOKEN=2.00xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 代码中使用

系统会自动检测环境变量，如果配置了access_token，会自动使用官方API：

```python
# 系统会自动选择使用官方API或移动端API
collector = WeiboCollector()
questions = collector.collect(config)
```

## 故障排查

### 1. access_token无效

**错误信息**: `error: invalid token`

**解决方法**:
- 检查access_token是否正确
- 检查access_token是否过期
- 重新进行OAuth授权获取新的access_token

### 2. API调用频率超限

**错误信息**: `error: rate limit exceeded`

**解决方法**:
- 降低请求频率
- 系统已实现速率限制，但可能仍需要进一步调整

### 3. 权限不足

**错误信息**: `error: insufficient_scope`

**解决方法**:
- 检查是否需要申请高级接口权限
- 检查用户是否授权了必要的Scope

## 参考文档

- [微博开放平台](https://open.weibo.com/)
- [微博API文档](https://open.weibo.com/wiki/微博API)
- [OAuth 2.0授权说明](https://open.weibo.com/wiki/授权机制说明)
- [接口访问权限说明](https://open.weibo.com/wiki/Rate-limiting)

