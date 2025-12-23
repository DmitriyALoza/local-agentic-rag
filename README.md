# AI-ELN: AI Electronic Lab Notebook

A local-first, agent-native Electronic Lab Notebook that allows scientists to upload experimental artifacts and query them conversationally using AI.

## Overview

AI-ELN enables scientists to:
- Upload lab documents (PowerPoint, Excel, Word, PDF)
- Automatically index and embed experimental data
- Ask natural language questions about experiments
- Receive answers with grounded citations from source documents

All processing happens locally with persistent vector storage.

## Features

- **Multi-Format Support**: PDF, PPTX, DOCX, XLSX
- **Intelligent Chunking**: Structure-aware text splitting (300-600 tokens with overlap)
- **Vector Search**: Semantic search powered by OpenAI embeddings
- **AI Agent**: GPT-4 powered assistant with function calling
- **Citation Tracking**: All answers include source references
- **Local-First**: Runs entirely on your machine with ChromaDB

## Requirements

- Python 3.13+
- OpenAI API key
- uv (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   cd agentic-rag-eln
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Configure environment variables**

   Edit the `.env` file and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-api-key-here
   ```

## Usage

### Running the Application

Start the Streamlit interface:
```bash
uv run streamlit run app/main.py
```

The application will open in your browser at `http://localhost:8501`

### Using the ELN

1. **Upload Documents**
   - Click "Browse files" in the sidebar
   - Select one or more documents (PDF, PPTX, DOCX, or XLSX)
   - Click "Process Documents" to index them
   - Wait for processing to complete (you'll see chunk counts)

2. **Ask Questions**
   - Type your question in the chat input at the bottom
   - The AI will search your documents and provide an answer
   - Citations will appear in the "Sources" dropdown

3. **Example Questions**
   - "What was the cell viability in experiment X?"
   - "List all documents that mention protein purification"
   - "What temperature was used in the PCR protocol?"
   - "Compare results from June and July experiments"

## Project Structure

```
ai-tutor/
├── app/
│   ├── main.py                 # Streamlit UI
│   ├── agent.py                # OpenAI Agent with function calling
│   ├── tools/
│   │   ├── ingest.py          # Document ingestion orchestrator
│   │   ├── retrieve.py        # Vector retrieval tool
│   │   └── metadata.py        # Metadata query tool
│   ├── ingestion/
│   │   ├── pptx.py            # PowerPoint parser
│   │   ├── pdf.py             # PDF parser
│   │   ├── docx.py            # Word parser
│   │   ├── xlsx.py            # Excel parser
│   │   ├── chunker.py         # Text chunking logic
│   │   └── metadata.py        # Metadata extraction
│   └── db/
│       └── chroma.py          # ChromaDB interface
├── data/
│   ├── raw_uploads/           # Original uploaded files
│   └── chroma/                # Vector database storage
├── prompts/
│   └── system.txt             # Agent system prompt
├── .env                       # Environment configuration
├── pyproject.toml             # Project dependencies
├── CLAUDE.md                  # Claude Code guidance
└── README.md                  # This file
```

## Architecture

```
User Query
    ↓
Streamlit UI
    ↓
OpenAI Agent (GPT-4)
    ↓
Function Calling
    ├── search_eln() → Retrieval Tool → ChromaDB
    ├── list_documents() → Metadata Query Tool
    └── get_document_info() → Metadata Query Tool
    ↓
Response with Citations
```

## Development

### Adding Dependencies

```bash
uv add <package-name>
```

### Running Tests

Testing can be done interactively through the Streamlit UI by uploading sample documents.

### Modifying the System Prompt

Edit `prompts/system.txt` to change how the AI agent behaves.

### Adjusting Chunk Size

Edit `app/ingestion/chunker.py` and modify the `TextChunker` initialization parameters:
- `min_chunk_size`: Minimum tokens per chunk (default: 300)
- `max_chunk_size`: Maximum tokens per chunk (default: 600)
- `overlap_size`: Token overlap between chunks (default: 75)

## Technical Details

### Document Processing Pipeline

1. **Parse**: Extract text from document using format-specific parser
2. **Chunk**: Split into 300-600 token chunks with 50-100 token overlap
3. **Enrich**: Add metadata (filename, section, timestamp, file type)
4. **Embed**: Generate vector embeddings using OpenAI `text-embedding-3-small`
5. **Store**: Save to ChromaDB with metadata

### Agent Behavior

The AI agent is instructed to:
- Use ONLY retrieved information from the ELN
- Never fabricate experimental data
- Always cite sources (filename + section/page/slide)
- Explicitly state "Not found in ELN" when information is unavailable
- Preserve exact numerical values and units

### Vector Search

- Embedding model: `text-embedding-3-small`
- Search returns top 5 most relevant chunks by default
- Supports metadata filtering (by file type, filename, etc.)

## Limitations (v0)

- Single user only (no authentication)
- Local execution only (no cloud deployment)
- No OCR for image-heavy PDFs
- No compliance features (21 CFR Part 11)
- Response time depends on document size and query complexity

## Future Enhancements

Potential additions for future versions:
- Multi-user support with authentication
- Cloud deployment (AWS/GCP)
- Advanced OCR for image-based documents
- Experiment timeline extraction
- SOP recommendation system
- Multi-agent workflows

## Troubleshooting

**"ModuleNotFoundError"**
- Run `uv sync` to ensure all dependencies are installed

**"OpenAI API Error"**
- Check that your API key is correctly set in `.env`
- Verify you have API credits available

**"No results found"**
- Ensure documents were successfully processed (check for success message)
- Try rephrasing your question
- Check that uploaded documents contain relevant text

**ChromaDB errors**
- Delete `data/chroma/` directory and re-upload documents
- Ensure you have write permissions in the project directory

## License

This project is for research and development purposes.

## Support

For issues or questions, please check:
- CLAUDE.md for development guidance
- .llm/AI-ELN_v0_PRD.md for product requirements
