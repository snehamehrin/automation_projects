# Knowledge Engine (PDF → Chroma → Chat)

MVP for a reusable personal knowledge engine. Ingest PDFs, chunk, embed, store in Chroma, and chat with your collection.

## Setup

1) Create virtual env and install deps
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2) Configure env
```bash
cp .env.example .env
# edit .env and add your OpenAI API key
```

## Run
```bash
streamlit run src/ui.py
```

- Pick a topic/collection name in the sidebar
- Upload one or more PDFs and click "Ingest PDFs"
- Ask questions in the chat box

## Notes
- Each topic gets its own Chroma collection so you can keep subjects isolated.
- Chunks include file metadata for citation.
- Later we can swap Chroma for Pinecone without changing the UI.
