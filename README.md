# 🎓 象数演易 — 数学教学动画 AI Agent

基于 **FastAPI + LangGraph + LLM** 的交互式数学教学动画自动生成系统。输入数学题目（文字/文档/图片），AI 自动生成带交互步骤的教学动画 HTML。

## ✨ 功能特性

- **多模态输入**：支持文字、文档（PDF/DOCX/TXT）、图片（LLM Vision OCR）三种输入方式
- **AI Agent 流水线**：LangGraph 状态机编排，分析→规划→逐步生成→组装→封面
- **实时进度**：异步任务架构，前端轮询显示生成进度
- **古风 UI**：水墨风格前端设计，响应式布局，支持移动端
- **教学动画**：Alpine.js + SVG + KaTeX，支持步骤切换、LaTeX 公式、交互动画
- **用户系统**：登录/注册（邀请码 + 手机验证码），用户协议/隐私政策
- **搜索功能**：模糊搜索已有案例，下拉展示匹配结果
- **封面生成**：自动为每个教学动画生成 SVG 封面

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI + Uvicorn |
| **AI Agent** | LangGraph + LangChain |
| **LLM** | MiMo / DeepSeek（OpenAI 兼容协议） |
| **前端动画** | Alpine.js + SVG + Tailwind CSS + KaTeX |
| **文档解析** | python-docx (DOCX)、PyMuPDF (PDF) |
| **存储** | 本地文件（HTML/JSON） |

## 📐 系统架构

```
用户输入（文字/文档/图片）
        ↓
   FastAPI 接收请求
        ↓
   LangGraph Agent（5 节点状态机）
   ┌──────────────────────────────────┐
   │ 1. analyze    → 题目分类/知识点  │
   │ 2. plan       → 动画方案设计     │
   │ 3. generate   → 逐步生成 HTML    │
   │    (每个步骤一次 LLM 调用)       │
   │ 4. assemble   → 模板组装         │
   │ 5. preview    → 生成封面 SVG     │
   └──────────────────────────────────┘
        ↓
   存储 HTML + 封面 → 返回 task_id
        ↓
   前端轮询进度 → iframe 渲染动画
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/teaching-animation-agent.git
cd teaching-animation-agent
```

### 2. 安装依赖

```bash
conda create -n agent-dev python=3.11
conda activate agent-dev
pip install fastapi uvicorn langgraph langchain-openai python-dotenv python-docx pymupdf httpx
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 填入你的 API Key：

```env
LLM_BASE_URL=https://api.xiaomimimo.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=mimo-v2.5-pro

# 可选：图像生成 API
# IMAGE_API_BASE=https://api.openai.com/v1
# IMAGE_API_KEY=sk-xxx
# IMAGE_MODEL=dall-e-3
```

### 4. 启动服务

```bash
python -m backend.main
```

访问 http://127.0.0.1:8080

## 📁 项目结构

```
teaching-animation-agent/
├── backend/
│   ├── main.py          # FastAPI 入口，路由定义
│   ├── agent.py         # LangGraph Agent（5 节点状态机）
│   ├── auth.py          # 用户认证（登录/注册/验证码）
│   ├── models.py        # Pydantic 数据模型
│   └── storage.py       # 任务存储（内存 + 磁盘持久化）
├── frontend/
│   ├── index.html       # 首页（案例展示 + 搜索 + 创建任务）
│   ├── video.html       # 动画播放页（进度 + iframe + 评论区）
│   └── auth.js          # 登录/注册弹窗
├── storage/             # 运行时数据（不上传）
│   ├── html/            # 生成的教学动画 HTML
│   ├── previews/        # 封面 SVG
│   └── metadata/        # 任务元数据 JSON
├── .env.example         # 环境变量模板
├── .gitignore
└── README.md
```

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/tasks` | 创建生成任务（form: prompt） |
| `GET` | `/api/tasks/{id}` | 查询任务状态 |
| `GET` | `/api/tasks/{id}/html` | 获取生成的 HTML |
| `GET` | `/api/tasks/{id}/preview` | 获取封面图 |
| `GET` | `/api/tasks` | 列出所有任务 |
| `POST` | `/api/parse-file` | 解析上传文件（PDF/DOCX/TXT/图片） |
| `POST` | `/api/auth/login` | 用户登录 |
| `POST` | `/api/auth/register` | 用户注册（邀请码） |

## 🔧 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com` |
| `LLM_API_KEY` | API Key | （无） |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `IMAGE_API_BASE` | 图像生成 API（选填） | （无） |
| `IMAGE_API_KEY` | 图像生成 Key（选填） | （无） |
| `IMAGE_MODEL` | 图像生成模型（选填） | （无） |

## 📝 License

MIT
