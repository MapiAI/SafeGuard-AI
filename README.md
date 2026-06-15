# 🛡️ SafeGuard AI

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

**AI-Powered Detection and Analysis of Toxic Communication Patterns**

SafeGuard AI helps users identify and understand potentially harmful communication patterns in personal, educational, and workplace contexts. The system analyzes messages and provides educational insights grounded in authoritative resources.

> ⚠️ **SafeGuard AI analyzes linguistic patterns only. It does not diagnose individuals, assign guilt, or provide legal or psychological advice. For privacy, avoid using real names in messages.**

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [AI Pipeline](#ai-pipeline)
- [Knowledge Base](#knowledge-base)
- [Ethical Principles](#ethical-principles)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)

---

## Overview

SafeGuard AI introduces **Behavioral Pattern Timeline** analysis — instead of evaluating single messages in isolation, the system tracks communication patterns over time, detecting escalation, recurring cycles, and emerging risks across a series of messages grouped in Cases.

Key features:

- Multi-label toxic communication classification
- PII anonymisation before any external AI call (GDPR-aware)
- Retrieval-Augmented Generation (RAG) grounded in educational sources
- Behavioral timeline and pattern analytics dashboard
- Educational chat assistant with daily rate limiting
- JWT-authenticated multi-user REST API

---

## Architecture

```
User Input (Message)
        ↓
PII Anonymisation — Microsoft Presidio
        ↓
Fine-tuned DistilBERT Gate — toxic / non-toxic
        ↓ (if toxic or uncertain)
Zero-shot Classifier — facebook/bart-large-mnli
→ 10 toxic communication categories + confidence scores
→ Risk score (avg across all 10 categories)
→ Risk level: none / low / medium / high
        ↓
RAG Retrieval — pgvector similarity search
→ Top 3 relevant educational chunks from knowledge base
        ↓
OpenAI GPT-4o-mini — RAG-grounded generation
→ Educational explanation (hedged language)
→ 3 response strategies: Assertive / Neutral / De-escalation
        ↓
PostgreSQL Storage
→ Analysis saved with categories, risk score, explanation, strategies
        ↓
Streamlit Dashboard
→ Timeline, pattern distribution, risk evolution
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Database | PostgreSQL 17 + pgvector |
| Authentication | JWT (python-jose + bcrypt) |
| AI Gate | Fine-tuned DistilBERT (civil_comments + custom examples) |
| AI Classifier | HuggingFace — facebook/bart-large-mnli (zero-shot) |
| AI Generator | OpenAI GPT-4o-mini |
| RAG | LangChain + pgvector + OpenAI text-embedding-3-small |
| PII Protection | Microsoft Presidio |
| Frontend | Streamlit + Plotly |
| Migrations | Alembic |

---

## Project Structure

```
safeguard-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py          # Register, login
│   │   │   │   ├── cases.py         # CRUD cases
│   │   │   │   ├── messages.py      # CRUD messages
│   │   │   │   ├── analysis.py      # AI analysis pipeline
│   │   │   │   └── assistant.py     # RAG educational assistant
│   │   │   └── dependencies.py      # JWT auth dependency
│   │   ├── core/
│   │   │   ├── config.py            # Environment settings
│   │   │   ├── security.py          # Password hashing, JWT
│   │   │   └── dependencies.py      # get_current_user
│   │   ├── db/
│   │   │   └── database.py          # SQLAlchemy engine, session
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── case.py
│   │   │   ├── message.py
│   │   │   ├── analysis.py
│   │   │   └── usage_log.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── case.py
│   │   │   ├── message.py
│   │   │   └── analysis.py
│   │   └── services/
│   │       ├── anonymizer.py        # Microsoft Presidio PII
│   │       ├── classifier.py        # DistilBERT gate + bart-large-mnli
│   │       ├── explainer.py         # OpenAI GPT-4o-mini
│   │       ├── rag_indexer.py       # Index knowledge base into pgvector
│   │       ├── rag_retriever.py     # Similarity search
│   │       └── finetune.py          # DistilBERT fine-tuning script
│   ├── main.py                      # FastAPI entry point
│   └── requirements.txt
├── frontend/
│   ├── app.py                       # Streamlit entry point + auth
│   ├── components.py                # Shared sidebar, auth check
│   ├── pages/
│   │   ├── 1_Cases.py
│   │   ├── 2_Analyze.py
│   │   ├── 3_Dashboard.py
│   │   └── 4_RAG_Assistant.py
│   └── .streamlit/
│       └── config.toml
├── data/
│   └── knowledge_base/              # Educational .txt documents for RAG
│       ├── healthy_relationships.txt
│       ├── coercive_control.txt
│       ├── gaslighting.txt
│       ├── emotional_abuse.txt
│       ├── manipulation_tactics.txt
│       ├── healthy_boundaries.txt
│       ├── bullying_workplace.txt
│       ├── workplace_mobbing.txt
│       ├── stalking.txt
│       ├── cyberbullying.txt
│       ├── assertive_communication.txt
│       ├── neutral_communication.txt
│       └── neutral_communication_examples.txt
├── models/
│   └── toxic_gate/                  # Fine-tuned DistilBERT (not in Git)
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 17 with pgvector extension
- OpenAI API key

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/safeguard-ai.git
cd safeguard-ai
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 3. Environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT secret key (minimum 32 characters) |
| `ALGORITHM` | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry in minutes (default: 30) |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini and embeddings |
| `HUGGINGFACE_API_KEY` | Optional — HuggingFace API key |

### 4. Database setup

```bash
psql -U your_username postgres
```

```sql
CREATE DATABASE safeguard_ai;
\c safeguard_ai
CREATE EXTENSION vector;
\q
```

### 5. Index the knowledge base

```bash
python -m app.services.rag_indexer
```

This chunks the educational documents and stores embeddings in pgvector.

### 6. Fine-tune the gate model (optional — pre-trained model included)

```bash
python -m app.services.finetune
```

Trains DistilBERT on civil_comments dataset + custom toxic communication examples. Takes approximately 5-10 minutes on a modern laptop.

---

## Running the Application

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

API available at: `http://localhost:8000`  
Swagger docs at: `http://localhost:8000/docs`  
Health check at: `http://localhost:8000/health`

### Frontend

```bash
cd frontend
streamlit run app.py
```

Frontend available at: `http://localhost:8501`

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT token |

### Cases

| Method | Endpoint | Description |
|---|---|---|
| GET | `/cases/` | List all cases for current user |
| POST | `/cases/` | Create a new case |
| GET | `/cases/{id}` | Get a specific case |
| PATCH | `/cases/{id}` | Update a case |
| DELETE | `/cases/{id}` | Delete a case |

### Messages

| Method | Endpoint | Description |
|---|---|---|
| GET | `/cases/{id}/messages/` | List all messages in a case |
| POST | `/cases/{id}/messages/` | Add a message to a case |
| GET | `/cases/{id}/messages/{msg_id}` | Get a specific message |
| PATCH | `/cases/{id}/messages/{msg_id}` | Update a message |
| DELETE | `/cases/{id}/messages/{msg_id}` | Delete a message |

### Analysis

| Method | Endpoint | Description |
|---|---|---|
| POST | `/cases/{id}/messages/{msg_id}/analyze` | Run full AI analysis on a message |
| GET | `/cases/{id}/messages/{msg_id}/analysis` | Retrieve stored analysis |

### Assistant

| Method | Endpoint | Description |
|---|---|---|
| POST | `/assistant/ask` | Ask an educational question (10/day limit) |
| GET | `/assistant/usage` | Check daily question usage |

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API status |
| GET | `/health` | Health check |
| GET | `/me` | Current user info |

Full interactive documentation available at `/docs` (Swagger UI).

---

## AI Pipeline

### Stage 0 — PII Anonymisation

Microsoft Presidio detects and replaces personally identifiable information before any text reaches external AI models:

| Original | Anonymised |
|---|---|
| John called me | `[PERSON]` called me |
| +39 02 1234567 | `[PHONE_NUMBER]` |
| maria@email.com | `[EMAIL_ADDRESS]` |

### Stage 1A — Toxic Gate (DistilBERT)

Fine-tuned DistilBERT classifies each message as toxic or non-toxic:
- `non-toxic` with confidence ≥ 0.92 → pipeline stops, risk level: `none`
- Otherwise → proceeds to zero-shot classification

### Stage 1B — Multi-label Classification (bart-large-mnli)

Zero-shot classification across 10 toxic communication categories:

| Category | Description |
|---|---|
| Control | Limiting personal freedom and autonomy |
| Manipulation | Exploiting feelings to influence behavior |
| Threat | Direct threats and intimidation |
| Psychological Pressure | Emotional coercion |
| Jealousy | Possessive behavior |
| Isolation | Separating from friends and family |
| Gaslighting | Reality distortion |
| Humiliation | Degradation and put-downs |
| Aggressive Language | Verbal aggression and insults |
| Coercion | Forced compliance |

**Risk score** = average confidence across all 10 categories (not just detected ones).  
**Risk level** = none / low / medium / high based on score thresholds.

### Stage 2 — RAG Retrieval

pgvector similarity search retrieves the top 3 most relevant educational chunks from the knowledge base based on the message content and detected categories.

### Stage 3 — Grounded Generation (GPT-4o-mini)

OpenAI GPT-4o-mini generates:
- **Explanation** — educational description of detected patterns using hedged language, grounded exclusively in retrieved documents
- **Response strategies** — three general communication approaches (Assertive, Neutral, De-escalation) with educational disclaimer

---

## Knowledge Base

The RAG knowledge base contains 90+ chunks from 13 educational documents sourced from:

| Source | Topics |
|---|---|
| thehotline.org | Coercive control, gaslighting, emotional abuse |
| loveisrespect.org | Healthy relationships, relationship spectrum |
| verywellmind.com | Manipulation tactics, healthy boundaries, stalking |
| acas.org.uk | Workplace bullying |
| allvoices.co | Workplace mobbing |
| stopbullying.gov | Bullying, cyberbullying |
| skillsyouneed.com | Assertive communication |

---

## Ethical Principles

SafeGuard AI is designed with Responsible AI principles:

- **Pattern analysis only** — the system analyzes linguistic patterns, never people
- **Hedged language** — responses always use "may suggest", "is often associated with", "could indicate"
- **RAG-grounded** — explanations are based exclusively on retrieved educational documents
- **PII protection** — personal information is anonymised before any external AI call
- **No diagnosis** — the system never labels individuals or provides clinical assessments
- **No legal advice** — the system never recommends reporting someone or taking legal action
- **Transparent limitations** — the system acknowledges uncertainty and encourages professional support

The ethical policy is embedded directly in the GPT system prompt and enforced at the architecture level through RAG-grounding.

---

## Known Limitations

- Zero-shot classification may produce false positives on ambiguous or context-dependent language
- The fine-tuned gate model was trained on a limited dataset and may miss subtle implicit threats
- Risk scoring produces a bimodal distribution (none or high) — medium/low risk requires more nuanced domain-specific training
- Social media language, sarcasm, emoji-based communication, and non-English input are not fully supported
- Single message analysis is inherently limited — the behavioral timeline across multiple messages provides more reliable insights

---

## Future Improvements

- Fine-tuned multi-label classifier on domain-specific relational communication data
- Support for additional languages (Italian, German, Spanish)
- Screenshot OCR ingestion for image-based messages
- WhatsApp and email export analysis
- Mobile application
- Export reports for professional counselors
- Human-in-the-loop review interface for uncertain classifications
- Deployment on Render + Supabase

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*SafeGuard AI — Built with care for responsible AI design.*
