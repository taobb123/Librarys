# 环境变量配置说明

## 快速配置

### Windows系统

编辑 `start-backend.bat` 文件，在脚本开头添加环境变量设置：

```bat
set JUHE_API_KEY=d309075150e27978571dcb7d8c48bacc
```

### Linux/Mac系统

在终端中设置：

```bash
export JUHE_API_KEY=d309075150e27978571dcb7d8c48bacc
```

## 配置说明

### 聚合数据API密钥

- **变量名**: `JUHE_API_KEY`
- **用途**: 用于访问聚合数据平台的各种API接口
- **当前配置**: `d309075150e27978571dcb7d8c48bacc`
- **支持的API**:
  - 微信热搜榜 API（接口ID: 737）
  - 其他聚合数据平台API

### 配置位置

环境变量可以在以下位置配置：

1. **启动脚本**（推荐）: `start-backend.bat`
2. **系统环境变量**: Windows系统设置 → 环境变量
3. **.env文件**: 使用python-dotenv加载（需要安装python-dotenv）

## 验证配置

启动后端服务后，查看控制台输出，应该看到：

```
[采集服务] 启用微信热搜采集器（聚合数据）
```

如果看到这条消息，说明配置成功。

## 注意事项

1. **API密钥安全**: 不要将API密钥提交到代码仓库
2. **免费额度**: 聚合数据普通会员每天50次免费调用
3. **自动启用**: 配置 `JUHE_API_KEY` 后，系统会自动启用微信热搜采集器

## 其他可选配置

### 启用第三方API聚合平台

```bash
set USE_THIRD_PARTY_API=true
```

### 微博开放平台配置

```bash
set WEIBO_APP_KEY=your_app_key
set WEIBO_APP_SECRET=your_app_secret
set WEIBO_ACCESS_TOKEN=your_access_token
```



