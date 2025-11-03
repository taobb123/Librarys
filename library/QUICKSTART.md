# 快速启动指南

## 前置要求

1. **Python 3.8+**
2. **Node.js 20.19+ 或 22.12+**
3. **MySQL 5.7+**

## 快速开始

### 1. 配置数据库

编辑 `backend/config.py`，设置MySQL连接信息：

```python
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DATABASE = 'library'
BOOKS_PATH = 'D:\\Books'  # 你的图书目录路径
```

### 2. 启动后端

```bash
# 安装Python依赖
pip install -r requirements.txt

# 启动Flask服务（会自动初始化数据库）
# 方式1：使用项目根目录的启动脚本（推荐）
python run.py

# 方式2：直接运行backend/app.py（需要从项目根目录运行）
python backend/app.py
```

后端将在 `http://localhost:5000` 启动

### 3. 启动前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:5173` 启动

### 4. 使用系统

1. 在浏览器中打开 `http://localhost:5173`
2. 点击左侧"扫描图书"按钮，扫描 `D:\Books` 目录
3. 从左侧列表中选择图书开始阅读

## 故障排查

### 后端无法启动

- **检查MySQL服务是否运行**
- **检查数据库配置是否正确**
- **确保有创建数据库的权限**

### 前端无法连接后端

- **检查后端是否已启动**（访问 `http://localhost:5000/api/health`）
- **检查前端 `.env` 文件中的 `VITE_API_BASE_URL` 配置**

### 无法加载EPUB

- **确保后端已正确配置CORS**
- **检查浏览器控制台是否有跨域错误**

## 下一步

- 添加更多电子书到 `D:\Books` 目录
- 使用书签功能保存阅读进度
- 为书签添加笔记

