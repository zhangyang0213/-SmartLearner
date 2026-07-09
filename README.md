# SmartLearner - 个性化学习与知识管理Agent

基于 RAG 架构的智能学习助手，集成课程问答、论文精读、知识库管理、学习路径规划四大核心模块。

## 功能特性

### 📚 课程专属问答助手
- 上传课件/教材（PDF、DOCX、PPTX、TXT、MD）
- 基于文档内容的智能问答
- 多轮对话支持
- 基于 Bloom 认知分类法的自动测验生成（选择题/判断题/简答题/论述题）
- 答案评估与反馈

### 📝 论文精读教练
- 自动结构化摘要（关键贡献、方法论、发现、局限性）
- 苏格拉底式深度提问（6大维度、3个深度层级）
- 回答评估与追问
- 论文导读指南生成
- 关联文献推荐与文献图谱
- 反面观点发现

### 🗂️ 个人知识库管家
- 多知识库创建与管理
- 混合检索（语义 + 关键词 + 混合模式）
- 跨知识库搜索
- 自然语言精准查询（LLM 优化查询词）
- 搜索结果重排序

### 🗺️ 学习路径规划师
- 根据目标定制学习计划
- 里程碑分解与每日任务生成
- 学习进度跟踪
- 学习统计（时长、连续天数、测验成绩）
- 基于进度的智能推荐
- 跨学科资源推荐

## 技术架构

```
┌─────────────────────────────────────────┐
│  前端: Next.js 14 + TailwindCSS         │
├─────────────────────────────────────────┤
│  后端: FastAPI + LangChain              │
├─────────────────────────────────────────┤
│  LLM: 阿里百炼 qwen-plus / qwen-turbo  │
│  Embedding: text-embedding-v3 (1024维)  │
│  向量库: FAISS                          │
│  存储: SQLite + JSON                    │
└─────────────────────────────────────────┘
```

## 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+
- [阿里云百炼 API Key](https://dashscope.console.aliyun.com/)

### 1. 克隆项目

```bash
git clone https://github.com/your-username/SmartLearner.git
cd SmartLearner
```

### 2. 配置后端

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
pip install -r requirements.txt
```

### 3. 启动后端

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 启动前端

```bash
cd ../frontend
npm install
npm run dev
```

### 5. 访问应用

- 前端: http://localhost:3000
- 后端 API 文档: http://localhost:8000/docs

### Docker 部署

```bash
# 在 .env 中配置 DASHSCOPE_API_KEY
docker-compose up -d
```

## 阿里云部署指南

### 推荐配置

| 资源 | 规格 | 月费用 |
|------|------|--------|
| ECS | 2核4G (通用算力型 u1) | ~¥17 |
| OSS | 500GB | ~¥10 |
| 百炼 API | qwen-plus | ~¥8 |

> 💡 300元代金券可覆盖首年基础费用，百炼赠送7000万免费Token

### 部署步骤

1. 购买阿里云 ECS（2核4G，Ubuntu 22.04）
2. 安装 Docker 和 Docker Compose
3. 克隆项目，配置环境变量
4. `docker-compose up -d`
5. 配置安全组开放 80/443 端口

## 项目结构

```
SmartLearner/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── core/                # 核心引擎
│   │   │   ├── rag_engine.py    # RAG 引擎
│   │   │   ├── document_parser.py
│   │   │   ├── vector_store.py
│   │   │   ├── embedding.py
│   │   │   └── llm.py
│   │   ├── modules/             # 功能模块
│   │   │   ├── course_qa/       # 课程问答
│   │   │   ├── paper_reader/    # 论文精读
│   │   │   ├── knowledge_base/  # 知识库管理
│   │   │   └── learning_path/   # 学习路径
│   │   └── api/                 # API 路由
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                 # Next.js 页面
│       ├── components/          # 组件
│       └── lib/                 # 工具函数
├── docker-compose.yml
├── Dockerfile
└── .gitignore
```

## 开源参考

| 项目 | 用途 |
|------|------|
| [RAGFlow](https://github.com/infiniflow/ragflow) | 文档解析参考 |
| [Dify](https://github.com/langgenius/dify) | 工作流架构参考 |
| [FastGPT](https://github.com/labring/FastGPT) | 知识库交互参考 |
| [LangChain](https://github.com/langchain-ai/langchain) | RAG 框架 |
| [LightRAG](https://github.com/HKUDS/LightRAG) | 知识图谱增强参考 |

## License

MIT License
