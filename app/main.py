"""
Local Agentic RAG - Main Streamlit Application
"""

import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.ingest import ingestion_tool
from app.agent import rag_agent
from app.tools.metadata import metadata_query_tool

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Local Agentic RAG",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files_list" not in st.session_state:
    st.session_state.uploaded_files_list = []
    # Load previously indexed files from ChromaDB
    indexed_files_result = metadata_query_tool.list_indexed_files()
    if indexed_files_result.get("success") and indexed_files_result.get("files"):
        st.session_state.uploaded_files_list = [
            f["filename"] for f in indexed_files_result["files"]
        ]

# Main title
st.title("📚 Local Agentic RAG")

# Show status of indexed documents
if st.session_state.uploaded_files_list:
    num_docs = len(st.session_state.uploaded_files_list)
    st.success(f"✓ {num_docs} document{'s' if num_docs != 1 else ''} indexed and ready for querying")
else:
    st.info("👉 Upload documents in the sidebar to get started")

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Document Upload")
    st.markdown("Upload your documents for AI-powered search")

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "pptx", "docx", "xlsx"],
        accept_multiple_files=True,
        help="Supported formats: PDF, PowerPoint, Word, Excel"
    )

    if uploaded_files:
        st.success(f"📄 {len(uploaded_files)} file(s) selected")

        # Upload button
        if st.button("Process Documents", type="primary"):
            with st.spinner("Processing documents..."):
                file_paths = []

                for uploaded_file in uploaded_files:
                    if uploaded_file.name not in st.session_state.uploaded_files_list:
                        # Save file to raw_uploads
                        upload_path = Path(os.getenv("UPLOAD_PATH", "./data/raw_uploads"))
                        upload_path.mkdir(parents=True, exist_ok=True)

                        file_path = upload_path / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        file_paths.append(str(file_path))

                # Ingest documents
                if file_paths:
                    result = ingestion_tool.ingest_multiple_documents(file_paths)

                    if result["successful"] > 0:
                        st.success(
                            f"✓ Successfully processed {result['successful']} file(s) "
                            f"({result['total_chunks']} chunks created)"
                        )

                        # Update uploaded files list
                        for file_result in result["results"]:
                            if file_result.get("success"):
                                filename = file_result["file"]
                                if filename not in st.session_state.uploaded_files_list:
                                    st.session_state.uploaded_files_list.append(filename)

                    if result["failed"] > 0:
                        st.warning(f"⚠ Failed to process {result['failed']} file(s)")
                        for file_result in result["results"]:
                            if not file_result.get("success"):
                                st.error(f"Error in {file_result['file']}: {file_result.get('error')}")
                else:
                    st.info("All selected files have already been processed.")

    # Display database statistics and indexed files
    if st.session_state.uploaded_files_list:
        st.markdown("---")

        # Get database stats
        stats = metadata_query_tool.get_collection_stats()
        if stats.get("success"):
            st.subheader("📊 Database Statistics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documents", stats.get("total_documents", 0))
            with col2:
                st.metric("Chunks", stats.get("total_chunks", 0))

        st.markdown("---")
        st.subheader("📄 Indexed Documents")
        st.caption("Documents available for querying")

        for filename in st.session_state.uploaded_files_list:
            st.text(f"✓ {filename}")

        # Add refresh button to reload file list
        if st.button("🔄 Refresh List", help="Reload indexed documents from database"):
            indexed_files_result = metadata_query_tool.list_indexed_files()
            if indexed_files_result.get("success") and indexed_files_result.get("files"):
                st.session_state.uploaded_files_list = [
                    f["filename"] for f in indexed_files_result["files"]
                ]
                st.rerun()

# Main chat interface
st.header("💬 Ask Questions")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("📚 Sources"):
                for source in message["sources"]:
                    st.markdown(f"- {source}")

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        if not st.session_state.uploaded_files_list:
            response = "Please upload documents first before asking questions."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            with st.spinner("Searching documents..."):
                # Query the agent
                # Build conversation history from session messages
                conversation_history = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state.messages[:-1]  # Exclude the current message
                ]

                # Get response from agent
                result = rag_agent.query(prompt, conversation_history)

                if result.get("success"):
                    response = result["response"]
                    sources = result.get("sources", [])

                    st.markdown(response)

                    # Display sources if available
                    if sources:
                        with st.expander("📚 Sources"):
                            for source in sources:
                                st.markdown(f"- {source}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources
                    })
                else:
                    error_response = f"Error: {result.get('response', 'Unknown error')}"
                    st.error(error_response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_response
                    })

# Footer
st.markdown("---")
st.caption("Local Agentic RAG - AI-powered document search and Q&A")
