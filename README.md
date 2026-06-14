## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 17 with pgvector extension
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/safeguard-ai.git
cd safeguard-ai

# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_lg

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start the server
uvicorn main:app --reload
```

### Database Setup

```bash
psql -U your_username postgres
CREATE DATABASE safeguard_ai;
\c safeguard_ai
CREATE EXTENSION vector;
\q
```

### Index Knowledge Base

```bash
python -m app.services.rag_indexer
```

### Fine-tune Gate Model (optional, model included)

```bash
python -m app.services.finetune
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /auth/register | Register a new user |
| POST | /auth/login | Login and get JWT token |
| GET | /cases/ | List all cases |
| POST | /cases/ | Create a new case |
| GET | /cases/{id} | Get a case |
| PATCH | /cases/{id} | Update a case |
| DELETE | /cases/{id} | Delete a case |
| GET | /cases/{id}/messages/ | List messages in a case |
| POST | /cases/{id}/messages/ | Add a message |
| POST | /cases/{id}/messages/{id}/analyze | Analyze a message |

Full API documentation available at `/docs` when the server is running.

## Ethical Principles

SafeGuard AI is designed with Responsible AI principles:

- **Pattern analysis only** — the system analyzes linguistic patterns, not people
- **Hedged language** — responses use "may suggest", "is often associated with"
- **RAG-grounded** — explanations are based exclusively on retrieved educational documents
- **PII protection** — personal information is anonymised before any external AI call
- **No diagnosis** — the system never labels individuals or provides clinical assessments

## Known Limitations

- Zero-shot classification may produce false positives on ambiguous language
- The fine-tuned gate model was trained on a limited dataset and may miss subtle threats
- Social media language, sarcasm, and emoji-based communication are not fully supported
- The system works best with English language input

## Future Improvements

- Fine-tuned multi-label classifier on domain-specific data
- Support for additional languages
- Screenshot and document upload (OCR)
- Mobile application
- Export reports for professional use