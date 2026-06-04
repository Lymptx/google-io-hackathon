# Google I/O Hackathon - AI Pipeline for Video Analysis

This project comprises two interconnected pipeline components built for the Google I/O Hackathon:

## Components

### Clip Ingestion Pipeline
**Built by:** Benjamin and Sampreeth

Handles the ingestion, processing, and summarization of video clips. This pipeline processes raw video data and generates tactical summaries for analysis.

Located in: `clip ingestion pipeline/`

### Analysis Query Pipeline
**Built by:** Ainesh

Provides querying and analysis capabilities over ingested clip data. This pipeline enables tactical analysis and pattern discovery from the processed video summaries.

Located in: `Analysis query pipeline/`

## Key Features

- **AI-driven soccer clip analysis platform** using RocketRide, Chroma vector database, and DeepSeek-v3 LLM; multi-specialist subagent architecture (passing, positioning, speed, defending, tactics) delivers structured coaching feedback across 5 performance dimensions with evidence-based scores and tactical adjustments

- **Semantic search pipeline** with MiniLM embeddings indexing 100+ video clip summaries and coaching principles; enables coaches to discover relevant training footage via natural language queries rather than manual video browsing, reducing clip discovery time

- **Modular RocketRide pipeline architecture** with three specialized workflows (clip indexing, tactics uploading, orchestration chat); decoupled data ingestion from inference using single-source components for scalable addition of new video libraries and coaching frameworks

- **Retrieval-augmented analysis system** combining clip evidence and uploaded team tactics into coaching recommendations; context-aware feedback by embedding both indexed clips and coach-uploaded principles in shared MiniLM vector space

- **Agent orchestrator** that intelligently routes coach questions to relevant specialist subagents and synthesizes multi-dimensional outputs into actionable coaching summaries with clip timestamps, combined skill scores, and targeted training adjustments

---

Each subproject operates independently but together form a complete AI-powered video analysis system for tactical sports insights.
