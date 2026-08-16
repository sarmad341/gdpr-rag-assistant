# GDPR Q&A Assistant — Ask the Regulation

![UI Screenshot](docs/ui_screenshot.png) *(Placeholder: Add a screenshot of the Next.js UI here!)*

## 📖 The Problem
Legal and regulatory text is notoriously dense. The GDPR (General Data Protection Regulation) is a massive 99-article document governing data privacy in the EU. For startup founders, developers, and small business owners, reading the entire regulation to find out if they need a Data Protection Officer or how long they have to report a data breach is a massive time sink.

**This project solves that problem.** It is a Retrieval-Augmented Generation (RAG) system that allows users to ask plain-English questions about the GDPR. Instead of just guessing, the system searches the actual, official legal text of the GDPR, retrieves the most relevant articles, and uses a Large Language Model (LLM) to generate a clear answer *grounded exclusively in the law*.

---

## 🎯 Reviewer Guide (Evaluation Criteria)

This project was built for the DataTalks.Club LLM Zoomcamp. To make grading easy, here is where you can find the implementation for each criterion:

- **Problem Description**: See the section above!
- **RAG Flow**: Handled in `backend/main.py`. The user's query is embedded and searched against a FAISS vector database and a BM25 keyword index (`backend/retriever.py`), and then sent to the Groq LLM API (`backend/generator.py`).
- **Retrieval Evaluation**: `backend/eval_retrieval.py` calculates Hit Rate and MRR comparing Vector Search vs Hybrid Search.
- **LLM Evaluation**: `backend/eval_llm.py` tests multiple prompt variants (Plain English vs Strict Legal Analyst) and evaluates their output.
- **Monitoring**: `backend/monitor.py` is a Streamlit dashboard that reads from a SQLite database (`monitoring/logs.db`) tracking every query, the LLM's response time, and thumbs up/thumbs down user feedback.
- **Containerization**: *(Coming soon in Phase 8 - Dockerfiles and docker-compose)*
- **Reproducibility**: See the "How to Run" section below.

---

## 🏗️ Architecture & Tech Stack

- **Data Pipeline**: Prefect (`backend/ingest.py`) parses the raw GDPR text and builds the indexes.
- **Retrieval (Hybrid)**: FAISS (Vector Semantic Search) + BM25 (Keyword Exact Match Search).
- **Backend API**: FastAPI serving the RAG pipeline.
- **LLM Engine**: Groq API (`llama-3.1-8b-instant`) for ultra-fast generation.
- **Frontend UI**: Next.js (React, TypeScript, TailwindCSS) with a premium dark-mode aesthetic.
- **Database**: SQLite for query logging and user feedback.

---

## 🚀 How to Run

### 1. Setup the Environment
Clone the repository and set up a Python virtual environment:
```bash
git clone https://github.com/sarmad341/gdpr-rag-assistant.git
cd gdpr-rag-assistant
python -m venv venv
venv\Scripts\activate  # (On Windows) or source venv/bin/activate (On Mac/Linux)
```

### 2. Configure API Keys
Create a `.env` file in the root directory and add your Groq API key (free at console.groq.com):
```env
GROQ_API_KEY=your_api_key_here
```

### 3. Build the Database (Ingestion)
Install dependencies and run the Prefect ingestion pipeline to build the FAISS and BM25 indexes:
```bash
pip install -r backend/requirements.txt
python backend/ingest.py
```

### 4. Start the Servers
You will need three terminal windows to run the full stack (make sure your `venv` is activated in all of them!).

**Terminal 1 (Backend):**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```

**Terminal 3 (Monitoring Dashboard):**
```bash
streamlit run backend/monitor.py
```

---

## 💡 Usage & Examples

Once the servers are running, open **http://localhost:3000** in your browser. 

Here are a few example questions you can ask the GDPR assistant:
1. *"What are the conditions for consent?"*
2. *"When is a data protection officer required?"*
3. *"What are the penalties for violating the GDPR?"*
4. *"Can I process data about someone's racial or ethnic origin?"*

The system will generate an answer and display the specific GDPR Article stamps that it used to formulate the response. 

### User Feedback
You can click the 👍 or 👎 buttons on any answer. This feedback is instantly logged to the SQLite database.

### The Admin Dashboard
Open **http://localhost:8501** to view the Streamlit Monitoring Dashboard. Here you can see a high-level overview of total queries, average latency, user feedback metrics, and a table of all historical questions and answers.

![Dashboard Screenshot](docs/dashboard_screenshot.png) *(Placeholder: Add a screenshot of the Streamlit dashboard here!)*
