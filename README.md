# Agent_JobSearch
这是一个LinkedIn求职Agent！下面是项目的介绍和技术选项。以及架构思路

## 🎯 **核心问题：是否需要RAG？**

**答案是：YES！强烈推荐使用RAG**

理由如下：
- **语义理解**：简历和职位描述需要理解语义相似性，而不仅仅是关键词匹配。例如"Python工程师"和"Python开发者"应该被识别为相似
- **向量搜索效率**：当职位数量达到数百个时，向量数据库可以快速检索最相关的Top K个职位（通常在毫秒级）
- **可扩展性**：未来可以扩展到技能图谱、公司文化匹配等维度

根据搜索结果，使用语义招聘技术的组织实现了40%更快的招聘时间和60%的假阳性减少。

---

## 🏗️ **完整系统架构设计**

### **1. 整体架构（推荐微服务架构）**

```
┌─────────────────────────────────────────────────────────────┐
│                     前端界面 (Next.js)                │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    API Gateway (FastAPI)                     │
└─────┬────────────┬────────────┬────────────┬────────────────┘
      │            │            │            │
┌─────▼──────┐ ┌──▼─────┐ ┌───▼──────┐ ┌───▼──────────┐
│ 简历分析    │ │LinkedIn │ │ 匹配引擎  │ │ 评分系统     │
│ 服务        │ │爬虫服务  │ │(RAG)     │ │ (LLM)       │
└─────┬──────┘ └──┬─────┘ └───┬──────┘ └───┬──────────┘
      │            │            │            │
      └────────────┴────────────┴────────────┘
                   │
    ┌──────────────▼──────────────────────────┐
    │      Vector Database (chromadb) │
    │      + 关系数据库 (SQLite)            │
    └─────────────────────────────────────────┘
```

### **2. 核心服务模块详细设计**

#### **模块 A: 简历分析服务**
```python
技术栈：
- 文档解析: PyPDF2 / pdfplumber / Azure Document Intelligence
- NLP处理: spaCy / transformers
- 结构化提取: LangChain DocumentLoaders

流程：
1. PDF/DOCX解析 → 文本提取
2. 信息抽取：
   - 个人信息（可选）
   - 教育背景（学校、专业、GPA）
   - 工作经历（公司、职位、技能、项目）
   - 技能清单（编程语言、框架、工具）
3. 生成向量嵌入 (Embeddings)
4. 存储到向量数据库
```

#### **模块 B: LinkedIn爬虫服务**
```python
推荐开源项目：
- py-linkedin-jobs-scraper (最成熟)
- JobSpy (支持多平台)

关键功能：
1. 基于用户需求构建查询：
   - 职位关键词
   - 地点
   - 经验级别 (internship/entry/mid/senior)
   - 发布时间 (24h/week/month)
   - 工作类型 (remote/onsite/hybrid)

2. 反爬虫策略：
   - 代理池轮换
   - 请求频率控制 (速率限制)
   - Undetected ChromeDriver
   - 随机User-Agent
```

#### **模块 C: RAG匹配引擎**
```python
技术栈：
- Vector DB: chromadb (本地开发用Chroma)
- Embeddings: OpenAI text-embedding-3-small / Sentence-Transformers
- RAG框架: LangChain / LlamaIndex

工作流程：
1. 简历向量化 → 存储为查询向量
2. 职位描述批量向量化 → 存储到Vector DB
3. 相似度搜索：
   - 使用余弦相似度 (Cosine Similarity)
   - 检索Top 50个候选职位
4. 重排序 (Re-ranking)：
   - 使用Cross-Encoder模型精排
   - 考虑权重因素：
     * 技能匹配度 40%
     * 经验匹配度 30%
     * 教育背景 20%
     * 其他因素 10%
```

#### **模块 D: LLM评分系统**
```python
技术栈：
- LLM: GPT-4 
- Prompt Engineering

评分维度：
1. 技能匹配 (0-10分)
   - 必需技能覆盖率
   - 加分技能数量
   
2. 经验匹配 (0-10分)
   - 年限要求
   - 行业相关度
   
3. 教育背景 (0-10分)
   - 学历要求
   - 专业相关性
   
4. 综合评价：
   - 优势分析
   - 不足之处
   - 申请建议
```

---

## 🛠️ **推荐技术栈**

### **Agent框架选择**

根据场景分析，我推荐：

| 框架 | 适用场景 | 优势 | 劣势 |
|------|---------|------|------|
| **LangGraph** ⭐推荐 | 复杂工作流，需要状态管理 | 精细控制、可视化、生产级 | 学习曲线陡 |


**用LangGraph + LangChain组合**

理由：
1. LangGraph的图结构天然适合"简历分析→搜索→匹配→评分"这种多步骤流程
2. LangChain生态丰富，工具集成方便
3. 支持Human-in-the-loop（用户可以在中间环节介入）

### **完整技术栈**

```python
# 核心框架
langchain==0.3.x
langgraph==0.3.x

# LLM
openai  # GPT-4
anthropic  # Claude (可选)

# 向量数据库
chromadb  # 本地开发

# Embeddings
sentence-transformers  # 本地模型
openai  # text-embedding-3-small

# LinkedIn爬虫
linkedin-jobs-scraper
selenium
undetected-chromedriver

# 文档处理
pypdf2
python-docx
pdfplumber

# Web框架
fastapi
uvicorn
nextjs  # 前端

# 数据处理
pandas
numpy

# 数据库
sqlalchemy
用轻量级数据库 SQLite
```

---

## 📊 **详细流程设计（LangGraph实现）**


**详细节点实现：**

1. **parse_resume_node**：解析简历，提取结构化信息
2. **scrape_linkedin_node**：基于用户偏好爬取职位（并行异步）
3. **vector_search_node**：RAG检索Top 50
4. **llm_scoring_node**：LLM深度评分Top 10
5. **generate_report_node**：生成最终报告

---

## 🌟 **GitHub开源项目推荐**

基于搜索结果，以下项目值得借鉴：

### **1. 直接可用的完整项目**

| 项目 | Stars | 特点 | GitHub链接 |
|------|-------|------|-----------|
| **linkedin_auto_jobs_applier_with_AI** | 🔥热门 | AI自动申请+简历定制 | [查看](https://github.com/jomacs/linkedIn_auto_jobs_applier_with_AI) |
| **RAG-based-job-search-assistant** | ⭐ | 使用RAG的求职助手 | [查看](https://github.com/kyosek/RAG-based-job-search-assistant) |
| **Auto_job_applier_linkedIn** | ⭐ | 自动化申请工具 | [查看](https://github.com/GodsScion/Auto_job_applier_linkedIn) |

### **2. 爬虫组件**

- **py-linkedin-jobs-scraper** - Python爬虫库（推荐）
- **JobSpy** - 多平台爬虫（LinkedIn, Indeed, Glassdoor等）

### **3. RAG参考实现**

- **Resume-Screening-RAG-Pipeline** - 简历筛选RAG流程

---

## 🚀 **快速开始路线图**

### **Phase 1: MVP (2-3周)**
```
Week 1:
- 搭建基础架构 (FastAPI + Next.js)
- 实现简历解析 (PyPDF2)
- 集成py-linkedin-jobs-scraper

Week 2:
- 实现RAG匹配 (Chroma + OpenAI Embeddings)
- 基础LLM评分 (GPT-4o)

Week 3:
- 前端界面优化
- 测试和调试
```

### **Phase 2: 优化 (2-3周)**
```
- 切换到LangGraph架构
- 添加re-ranking层
- 优化prompt
- 添加缓存机制
```



---

## ⚠️ **关键注意事项**

1. **LinkedIn反爬虫**：
   - 使用代理池
   - 控制请求频率（建议10-20秒/请求）
   - 遵守robots.txt
   - 考虑使用LinkedIn官方API（需付费）

2. **成本优化**：
   - Embeddings用本地模型 (sentence-transformers)
   - LLM评分只用于Top 10，而不是所有职位
   - 实现缓存避免重复计算

3. **隐私和合规**：
   - 明确数据使用条款
   - 遵守GDPR/CCPA（如适用）
   - 不存储敏感个人信息

---

必须要的：
✅ 简历解析
✅ LinkedIn爬虫（带频率控制）
✅ RAG向量匹配（Chroma）
✅ LLM评分
✅ UI（Next.js）
✅ 结果导出

可选的：
⭕ 简单日志（推荐）
⭕ 结果缓存（推荐）
⭕ 批量处理（省钱）

不需要的：
❌ LangSmith
❌ 用户系统
❌ 数据库集群
❌ 负载均衡
❌ CI/CD


## 🚀 快速开始
1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量（OpenAI API Key）
4. 运行：`python main.py`