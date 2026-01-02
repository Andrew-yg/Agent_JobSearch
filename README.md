# 🎯 Agent JobSearch

Next.js + FastAPI intelligent job search agent that analyzes your resume, scrapes LinkedIn jobs, and uses RAG + GPT-4 to find your best matches.

[Getting Started](#-getting-started) · [Architecture](#-architecture) · [Key Features](#-key-features) · [Report Bug](https://github.com/Andrew-yg/Agent_JobSearch/issues)

---

## 📑 Table of Contents
- [About the Project](#-about-the-project)
  - [What Makes It Special?](#what-makes-it-special)
  - [Built With](#built-with)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
- [Running the Stack](#-running-the-stack)
- [Usage Walkthrough](#-usage-walkthrough)
- [API & Services](#-api--services)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🧠 About the Project

Agent JobSearch is an intelligent job search assistant that automates the tedious process of finding relevant job opportunities on LinkedIn. Built with a **LangGraph state machine architecture**, it doesn't just scrape jobs—it thinks like a human recruiter, analyzing page structure dynamically and matching jobs to your resume using semantic understanding.

### What Makes It Special?

The platform leverages **Retrieval Augmented Generation (RAG)** and **LangGraph orchestration** to create an intelligent job matching system where:

- **Resumes are vectorized** and stored in ChromaDB for semantic search
- **LinkedIn pages are analyzed by GPT-4** to dynamically identify page structure (no hardcoded selectors!)
- **Jobs are matched using cosine similarity** in vector space, not keyword matching
- **Each job is scored by GPT-4** on multiple dimensions (skills, experience, education)
- **Browser automation with Playwright** connects to your existing Chrome session for seamless LinkedIn access

### Built With

- [Next.js 14](https://nextjs.org/) - Frontend React framework
- [TypeScript](https://www.typescriptlang.org/) - Type-safe development
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance Python API
- [LangGraph](https://github.com/langchain-ai/langgraph) - State machine orchestration
- [LangChain](https://langchain.com/) - LLM application framework
- [ChromaDB](https://www.trychroma.com/) - Vector database for RAG
- [OpenAI GPT-4](https://openai.com/) - Page analysis, data extraction, job scoring
- [Playwright](https://playwright.dev/) - Browser automation via CDP

---

## ✨ Key Features

### 📄 Intelligent Resume Processing
- PDF upload with automatic text extraction using PyPDF2 and pdfplumber
- Skill extraction and categorization
- Resume vectorization with OpenAI embeddings (`text-embedding-3-small`)
- Persistent storage in ChromaDB for fast similarity search

### 🤖 LangGraph State Machine Agent
The core innovation—a **5-node state machine** that intelligently navigates LinkedIn:

```
analyze_page → validate_selectors → browse_jobs → validate_data → pagination
      ↑              ↓ (failure)                           ↓
      └──────────────┘                              (next page) ──→ analyze_page
```

| Node | Function |
|------|----------|
| `analyze_page` | GPT-4 analyzes page HTML, identifies CSS selectors dynamically |
| `validate_selectors` | Playwright tests selectors, collects job card elements |
| `browse_jobs` | Clicks each job card individually, extracts details from panel |
| `validate_data` | Checks data quality, ensures required fields exist |
| `pagination_handler` | Navigates to next page, handles multi-page scraping |

### 🔍 RAG-Powered Job Matching
- Jobs are vectorized and stored in ChromaDB
- Resume vector queries job collection using cosine similarity
- Top 50 candidates retrieved in milliseconds
- Semantic matching—"Python Engineer" matches "Python Developer"

### 🎯 GPT-4 Job Scoring
Each matched job is deeply analyzed by GPT-4 with weighted scoring:
- **Skills Match (40%)** - Technical skill overlap analysis
- **Experience Match (30%)** - Work history relevance
- **Education Match (20%)** - Academic background fit
- **Overall Score (10%)** - Holistic assessment

### 🌐 Real-Time Progress Streaming
- Server-Sent Events (SSE) for live progress updates
- Step-by-step visibility: Browser init → Job scraping → RAG matching → Scoring
- Error handling with actionable error messages

---

## 🧱 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                           │
│              Upload Resume │ Search Jobs │ View Results         │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API + SSE
┌────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                               │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│ Resume       │ LangGraph    │ RAG Engine   │ LLM Scorer        │
│ Parser       │ Job Agent    │ (ChromaDB)   │ (GPT-4)           │
└──────────────┴──────────────┴──────────────┴───────────────────┘
       │               │               │              │
       ▼               ▼               ▼              ▼
   PyPDF2        Playwright        ChromaDB      OpenAI API
                 (CDP→Chrome)    (Vector Store)
```

**Service Components:**
- `resume_parser.py` - PDF ingestion, text extraction, embedding generation
- `langgraph_agent.py` - State machine for intelligent LinkedIn browsing
- `rag_engine.py` - ChromaDB operations, similarity search
- `llm_scorer.py` - GPT-4 job evaluation and scoring
- `browser_agent.py` - Playwright browser connection management

---

## 🚀 Getting Started

### Prerequisites

- **Node.js 18+** (for Next.js frontend)
- **Python 3.10+** (for FastAPI backend)
- **Google Chrome** (for LinkedIn browsing via CDP)
- **OpenAI API Key** with GPT-4 access

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Andrew-yg/Agent_JobSearch.git
cd Agent_JobSearch

# 2. Install frontend dependencies
cd frontend
npm install

# 3. Install backend dependencies
cd ../backend
pip install -r requirements.txt

# 4. Copy env template
cp .env.example .env
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
OPENAI_API_KEY=sk-your-openai-api-key
USE_PLAYWRIGHT_MCP=false
```

---

## 🏃 Running the Stack

**Step 1: Start Chrome with Remote Debugging**

```bash
# macOS
open -a "Google Chrome" --args --remote-debugging-port=9222

# Windows
chrome.exe --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

**Step 2: Log in to LinkedIn** in the opened Chrome window.

**Step 3: Start the Backend**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Step 4: Start the Frontend**

```bash
cd frontend
npm run dev
```

**Step 5: Open** http://localhost:3000

Health checks available at:
- Backend: `GET http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

---

## 🧭 Usage Walkthrough

1. **Upload Resume** - Upload your PDF resume. The system extracts text, identifies skills, and creates vector embeddings.

2. **Configure Search** - Enter job keywords, location, experience level, and other filters.

3. **Start Search** - Click search to trigger the LangGraph agent. Watch real-time progress as it:
   - Navigates to LinkedIn Jobs
   - Analyzes page structure with GPT-4
   - Browses each job card individually
   - Extracts detailed job information

4. **View Matches** - RAG matching finds semantically similar jobs. GPT-4 scores each match.

5. **Review Results** - See top 10 jobs with detailed scores and analysis for each.

---

## 🔌 API & Services

### FastAPI Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload resume PDF |
| `POST` | `/api/search` | Start job search (SSE stream) |
| `GET` | `/health` | Backend health check |

### SSE Event Types

```javascript
// Progress update
{"step": 2, "total": 4, "status": "processing", "message": "Found 15 jobs..."}

// Job found
{"type": "job", "data": {...}}

// Search complete
{"type": "result", "data": {"top_jobs": [...], "total_jobs_found": 50}}
```

### Python Services

| Service | File | Purpose |
|---------|------|---------|
| Resume Parser | `resume_parser.py` | PDF extraction, vectorization |
| LangGraph Agent | `langgraph_agent.py` | Intelligent browser automation |
| RAG Engine | `rag_engine.py` | Vector search, job matching |
| LLM Scorer | `llm_scorer.py` | GPT-4 job evaluation |
| Browser Agent | `browser_agent.py` | Chrome CDP connection |

---

## 🗺 Roadmap

- [ ] Support for additional job boards (Indeed, Glassdoor)
- [ ] Cover letter generation based on job match analysis
- [ ] Application tracking and status management
- [ ] Multi-resume support for different job types
- [ ] Chrome extension for one-click job saving
- [ ] Docker-compose for simplified deployment

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is for educational purposes. Please contact the maintainers before commercial use.

---

## 📫 Contact

- **Project Link**: [https://github.com/Andrew-yg/Agent_JobSearch](https://github.com/Andrew-yg/Agent_JobSearch)
- **Issues**: [Report a bug](https://github.com/Andrew-yg/Agent_JobSearch/issues)

---

## 🙌 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for state machine orchestration
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Playwright](https://playwright.dev/) for reliable browser automation
- [Best-README-Template](https://github.com/othneildrew/Best-README-Template) for README inspiration

Happy job hunting! 🚀