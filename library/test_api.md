# API测试指南

## 测试后端API

后端应该运行在 `http://localhost:5000`

### 1. 健康检查
```bash
curl http://localhost:5000/api/health
```
或浏览器访问：`http://localhost:5000/api/health`

预期响应：
```json
{
  "status": "ok",
  "message": "Library API is running"
}
```

### 2. 获取图书列表
```bash
curl http://localhost:5000/api/books/list
```

### 3. 获取分类列表
```bash
curl http://localhost:5000/api/books/categories
```

### 4. 扫描图书目录
```bash
curl -X POST http://localhost:5000/api/books/scan
```

## 接下来

1. **确保MySQL数据库已配置并运行**
   - 检查 `backend/config.py` 中的数据库配置
   - 确保MySQL服务正在运行

2. **启动前端**
   ```bash
   cd frontend
   npm install  # 如果还没安装依赖
   npm run dev
   ```

3. **访问前端应用**
   - 浏览器打开：`http://localhost:5173`
   - 点击"扫描图书"按钮添加图书
   - 开始阅读！

