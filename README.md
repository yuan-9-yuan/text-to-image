# AI 文生图应用

用户输入文字描述，AI 生成图片。管理员可在后台查看所有生成记录。

## 快速部署（推荐）

### 一键部署到 Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/I6zPes?referralCode=your-code)

或手动部署：

1. 注册 [Railway](https://railway.app/)（GitHub 登录，免费额度足够）
2. 点击 **New Project** → **Deploy from GitHub repo**
3. 添加环境变量：
   - `AGNES_API_KEY` — 你的 Agnes AI API 密钥
   - `ADMIN_PASSWORD` — 管理后台密码
4. 部署完成后，Railway 会给你一个 `https://xxx.up.railway.app` 的域名
5. 把这个域名发给用户即可使用

## 本地运行

```bash
# 1. 安装 Python 3.9+
# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置环境变量
# Windows PowerShell:
$env:AGNES_API_KEY="你的密钥"
$env:ADMIN_PASSWORD="你的密码"

# 4. 启动
python app.py

# 5. 浏览器访问 http://localhost:5000
```

## 使用说明

### 用户端
- 访问首页，输入文字描述，点击"生成"按钮
- 等待 10-30 秒即可看到生成的图片
- 支持下载和复制图片

### 管理后台
- 访问 `/admin` 路径
- 输入你设置的 `ADMIN_PASSWORD` 登录
- 查看所有用户提交的文字和生成的图片
- 支持删除记录

## 文件结构

```
├── app.py              # 主程序
├── requirements.txt    # Python 依赖
├── Procfile            # Railway 部署配置
├── runtime.txt         # Python 版本
├── .env.example        # 环境变量示例
├── templates/
│   ├── index.html      # 用户页面
│   ├── admin.html      # 管理后台
│   └── admin_login.html # 登录页面
└── static/
    └── style.css       # 自定义样式
```

## 技术栈

- 后端：Python Flask
- 前端：Tailwind CSS (CDN)
- 数据库：SQLite
- AI 模型：agnes-image-2.1-flash (via Agnes AI API)
- 部署：Railway / Render
