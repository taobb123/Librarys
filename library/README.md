# 本地图书阅览系统

## 技术栈
- 后端：Python Flask
- 数据库：MySQL
- 前端：Vue.js 3 + TypeScript

## 功能特性
- ✅ 图书分类管理（文学、金融、科技、历史、艺术）
- ✅ 在线阅读支持（PDF、EPUB）
- ✅ 书签和笔记功能
- ⏳ 问题追踪管理（待实现）

## 项目结构
```
library/
├── backend/          # Flask后端
│   ├── app.py       # Flask应用入口
│   ├── config.py    # 配置文件
│   ├── models/      # 数据库模型
│   │   ├── db.py    # 数据库连接
│   │   ├── book_model.py
│   │   └── bookmark_model.py
│   └── api/         # API路由
│       └── books.py
├── frontend/        # Vue.js前端
│   ├── src/
│   │   ├── api/     # API服务
│   │   ├── components/ # 组件
│   │   ├── stores/  # Pinia状态管理
│   │   └── views/   # 页面视图
│   └── package.json
├── requirements.txt # Python依赖
└── README.md
```

## 安装说明

### 后端

1. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置MySQL数据库：
   - 确保MySQL服务已启动
   - 修改 `backend/config.py` 中的数据库配置：
     ```python
     MYSQL_HOST = 'localhost'
     MYSQL_PORT = 3306
     MYSQL_USER = 'root'
     MYSQL_PASSWORD = 'your_password'
     MYSQL_DATABASE = 'library'
     ```

3. 配置图书路径：
   - 修改 `backend/config.py` 中的 `BOOKS_PATH`，默认：`D:\Books`

4. 运行后端：
   ```bash
   python backend/app.py
   ```
   后端将在 `http://localhost:5000` 启动

### 前端

1. 进入前端目录：
   ```bash
   cd frontend
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 配置API地址（可选）：
   创建 `frontend/.env` 文件：
   ```
   VITE_API_BASE_URL=http://localhost:5000
   ```

4. 启动开发服务器：
   ```bash
   npm run dev
   ```
   前端将在 `http://localhost:5173` 启动（Vite默认端口）

## 使用说明

1. **扫描图书**：
   - 点击左侧"扫描图书"按钮
   - 系统会自动扫描 `D:\Books` 目录下的PDF、EPUB、AZW3、MOBI文件
   - 扫描的图书会自动添加到数据库

2. **浏览图书**：
   - 左侧显示所有图书列表
   - 可以按分类筛选（文学、金融、科技、历史、艺术）
   - 点击图书即可在右侧打开阅读

3. **阅读图书**：
   - PDF格式：使用浏览器原生PDF阅读器
   - EPUB格式：使用EPUB.js在线阅读
   - 其他格式：提供下载链接

4. **书签和笔记**：
   - 点击"添加书签"按钮可以保存当前阅读位置
   - 可以为书签添加笔记
   - 在书签面板中可以查看、跳转和删除书签

## 数据库表结构

### categories（分类表）
- 文学、金融、科技、历史、艺术字段

### books（图书表）
- id, title, file_path, file_format
- author, country, year, category
- file_size, created_at, updated_at

### bookmarks（书签表）
- id, book_id, page_number, position
- note, created_at, updated_at

### questions（问题表，待实现）
- 数据源、热度、趋势、兴趣、待办、已完成

## 注意事项

- 确保MySQL服务已启动
- 确保图书目录路径正确（默认：`D:\Books`）
- EPUB格式需要后端支持CORS
- PDF格式建议使用现代浏览器

## 待实现功能

- [ ] 问题管理功能
- [ ] 社交平台API集成（微博、Twitter、Reddit）
- [ ] AZW3和MOBI格式的在线阅读支持
- [ ] 图书搜索功能
- [ ] 阅读进度保存
- [ ] 更多格式转换支持
