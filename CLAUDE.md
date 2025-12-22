# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-ELN (ai-tutor) is a local-first, agent-native Electronic Lab Notebook that allows scientists to upload experimental artifacts (PowerPoint, Excel, Word, PDF) and query them conversationally using an OpenAI Agent.

**Core Concept:** Scientists upload lab documents, the system indexes them in a local vector database, and an AI agent answers questions about experiments with grounded citations.

## Tech Stack

- **Language:** Python 3.14+ (requires-python = ">=3.14")
- **Package Manager:** uv (NOT pip)
- **UI Framework:** Streamlit
- **Agent Framework:** OpenAI Agent SDK
- **Vector Database:** ChromaDB (local persistent mode)
- **LLM Provider:** OpenAI
- **Document Processing:** pypdf, python-docx, python-pptx, pandas, openpyxl

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment (if needed manually)
source .venv/bin/activate  # Unix/Mac
```

### Running the Application
```bash
# Start Streamlit UI
uv run streamlit run app/main.py
```

### Package Management
```bash
# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Update dependencies
uv lock
```

## Architecture

### System Flow
```
Streamlit UI → OpenAI Agent → Tool Calls → ChromaDB (local)
```

No separate backend server. Everything runs locally.

### Directory Structure (Planned)
```
app/
├── main.py              # Streamlit entry point
├── agent.py             # OpenAI Agent setup and configuration
├── tools/               # Agent tools
│   ├── ingest.py        # Document ingestion tool
│   ├── retrieve.py      # Vector retrieval tool
│   └── metadata.py      # Metadata management tool
├── ingestion/           # Format-specific parsers
│   ├── pptx.py          # PowerPoint parser
│   ├── pdf.py           # PDF parser (with OCR fallback)
│   ├── docx.py          # Word parser
│   └── xlsx.py          # Excel parser
└── db/
    └── chroma.py        # ChromaDB interface

data/
├── raw_uploads/         # Original uploaded files
└── chroma/              # ChromaDB persistent storage

prompts/
└── system.txt           # Agent system prompt
```

## Key Implementation Details

### Document Ingestion
- **Supported Formats:** .pptx, .xlsx, .docx, .pdf
- **Chunking:** 300-600 tokens per chunk with 50-100 token overlap
- **Metadata per chunk:** filename, file type, upload timestamp, section/slide/sheet
- Chunking must respect document structure (e.g., don't split tables)

### Agent Behavior
The OpenAI Agent follows this flow:
1. Interpret user's natural language question
2. Retrieve relevant chunks via retrieval tool
3. Synthesize answer from retrieved context only
4. Provide citations (filename + section)
5. If answer not found: explicitly state "Not found in ELN."

**Critical Rule:** Agent must NEVER fabricate experimental values or data.

### Vector Store Configuration
- **Database:** ChromaDB in local persistent mode
- **Embeddings:** OpenAI text embeddings (default)
- **Storage Location:** `data/chroma/`

### System Prompt (v0)
```
You are an AI lab notebook assistant.
Use only retrieved ELN context.
Always cite source filename and section.
If the answer is not present, say: "Not found in ELN."
Do not fabricate experimental values.
```

## Development Phases

- **Phase 0:** Repository + UI scaffold
- **Phase 1:** Document ingestion + indexing
- **Phase 2:** Agent query + retrieval
- **Phase 3:** UX polish

## Non-Functional Requirements

- Response latency < 2s locally
- Deterministic ingestion (same file = same chunks)
- Transparent citations in all answers
- Fully local execution (no cloud dependencies)
- High iterability for rapid development

## Environment Variables

Required in `.env`:
- `OPENAI_API_KEY` - OpenAI API key for embeddings and agent

## Important Constraints (v0)

**Out of Scope:**
- Multi-user authentication
- Cloud hosting (AWS/GCP)
- 21 CFR Part 11 compliance
- SOP enforcement
- Experiment graph reasoning

These are explicitly non-goals for v0 to maintain rapid iteration.
