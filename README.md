# Health & Fitness AI Companion

An agent-based RAG chatbot for YouTube videos in the health, fitness, and nutrition space. It doesn't just answer questions about a video — it fact-checks claims against trusted sources, extracts structured visual summaries from recipe videos, and works across a growing, multi-topic library of videos.

**Live app:** https://health-fitness-qa-bot-frontend.onrender.com
**Backend API:** https://health-fitness-qa-bot-backend.onrender.com

> The backend runs on Render's free tier and may take ~30–60s to wake up on the first request after a period of inactivity.

---

## The niche

Built on top of an open "YouTube video Q&A chatbot" brief, specialized around two personal problems:

- **Health & nutrition claims** — videos make a lot of claims with no easy way to check which ones hold up
- **Sport injury recovery** — long waits for medical appointments, meanwhile searching YouTube for advice with no way to judge how reliable it is

The result: a multi-topic video library spanning nutrition and sports recovery, where every answer is grounded in the source video, fact-checked against trusted knowledge, and — for recipes — turned into a structured, visual nutrition summary.

---

## Architecture

```
User (YouTube link or question)
        │
        ▼
Ingestion & processing — transcript extraction, cleaning, chunking, metadata
        │
        ▼
Vector DB (Chroma) — multi-topic, hybrid chunking (per-video: time-based or semantic)
        │
        ▼
Agent (7 tools) ── Knowledge base + web search (fact-check fallback chain)
        │        └─ LangSmith (tracing + evaluation, runs in parallel)
        ▼
Retrieval · Content tools · Fact-check
        │
        ▼
LLM synthesis
        │
        ▼
Output UI — chat, sidebar, hub, recipe view
```

**Stack:** Python / FastAPI backend, LangChain agent (GPT-4o-mini), Chroma vector DB, LangSmith for tracing & evaluation, React (Vite) frontend, deployed on Render.

---

## Agent tools

The agent decides which tool to use per question — it's not a fixed pipeline.

| Tool | What it does |
|---|---|
| Retrieval | Semantic search over video transcript chunks |
| Multi-query search | Rephrases the question a few ways, searches with all of them, merges results |
| Timestamp lookup | Returns the chunk covering a specific point in the video |
| Summary | General or technical (structured) summary of a video |
| Video metadata | Title, channel, upload date, length, tags |
| Fact-check | Checks a claim against a curated knowledge base, falls back to live web search, then general LLM knowledge |
| Recipe nutrition | Extracts ingredients, steps, and estimated calories/protein/carbs/sugar from a recipe video's transcript |

Plus conversation memory (SQLite-backed, survives a server restart).

---

## Two decisions worth calling out

**Hybrid chunking.** The MVP used fixed 30-second time windows. A semantic chunking method (adaptive, percentile-based similarity threshold) was added and evaluated head-to-head against the time-based method, per video, using a small LLM-judge retrieval evaluator. There was no universal winner — the system now picks the better-performing method automatically for each new video, rather than committing to one approach globally.

**Fact-check fallback chain.** Started as LLM-only (with an honest disclaimer). Evolved into a 3-stage fallback: curated knowledge base → live web search (Tavily) → general LLM knowledge, with a transparent source note on every fact-check answer. Only topics with real curated data use the knowledge base — other topics fall straight to web search, so the system scales to new topics without manual setup.

---

## Evaluation

LangSmith traces every agent run and scores it against a small test dataset (tool selection, groundedness, format consistency, retrieval relevance). Iteration was evaluation-driven throughout — for example, a fact-check output-format bug took three rounds to fully resolve (sharper prompt → structured output → thread isolation + explicit pass-through instruction), each round re-verified against the dataset rather than by eyeballing answers. The same approach later caught and fixed a retrieval bug (wrong-topic chunks) and a recurrence of the formatting issue after multi-topic support was added.

---

## Bonus features

- **Multi-topic library** — a hub page across two topics (nutrition, sports recovery), each with multiple videos, searchable individually or across all videos in a topic
- **Visual recipe breakdown** — one click on a cooking video shows ingredients, steps, and calorie/protein/carb/sugar bars, extracted directly from the transcript (no external nutrition database)
- **Sidebar + hub UI** — topic/video selection, visible feature overview, persistent chat history (stored client-side, mapped to server-side conversation threads)
- **Persistent memory** — SQLite-backed conversation checkpointing

---

## Known limitations / deliberately out of scope

- **LangGraph routing** — explicit graph-based control over the fact-check decision path; not built, noted as a natural next step
- **Voice input** — not built
- **Live video ingestion from the app** — the backend pipeline for this was built, but not wired into the live demo; processing a new video takes several minutes, which was judged too risky to demo live under a time limit. New videos are currently added via notebook scripts (`notebooks/`)

---

## Running locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Requires a `.env` file in the project root with `OPENAI_API_KEY`, `TAVILY_API_KEY`, and `LANGSMITH_API_KEY`.

---

## Project structure

```
backend/          FastAPI app, agent, tools, config
frontend/          React (Vite) app — chat, sidebar, hub, recipe view
notebooks/         Data ingestion, chunking, evaluation, and experimentation notebooks
data/              Transcripts, video metadata, Chroma vector store
```
