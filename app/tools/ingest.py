"""
Document Ingestion Tool
Orchestrates parsing, chunking, embedding, and storage of documents
"""

import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI

from app.ingestion.pdf import PDFParser
from app.ingestion.pptx import PowerPointParser
from app.ingestion.docx import WordParser
from app.ingestion.xlsx import ExcelParser
from app.ingestion.chunker import TextChunker
from app.ingestion.metadata import MetadataExtractor
from app.db.chroma import chroma_client

load_dotenv()


class DocumentIngestionTool:
    """Tool for ingesting documents into the RAG system"""

    def __init__(self):
        """Initialize the ingestion tool with parsers and chunker"""
        self.parsers = {
            "pdf": PDFParser(),
            "pptx": PowerPointParser(),
            "docx": WordParser(),
            "xlsx": ExcelParser()
        }
        self.chunker = TextChunker()
        self.metadata_extractor = MetadataExtractor()
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def ingest_document(self, file_path: str) -> Dict:
        """
        Ingest a single document

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary with ingestion results and statistics
        """
        path = Path(file_path)
        file_type = path.suffix.lstrip('.').lower()

        if file_type not in self.parsers:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_type}",
                "file": path.name
            }

        try:
            # Step 1: Parse document
            parser = self.parsers[file_type]
            parsed_chunks = parser.parse(file_path)

            if not parsed_chunks:
                return {
                    "success": False,
                    "error": "No content extracted from document",
                    "file": path.name
                }

            # Step 2: Chunk the parsed content
            chunked_documents = self.chunker.chunk_document(parsed_chunks)

            # Step 3: Enrich metadata
            file_info = self.metadata_extractor.extract_file_info(file_path)
            upload_timestamp = file_info["upload_timestamp"]

            for chunk in chunked_documents:
                chunk["metadata"] = self.metadata_extractor.enrich_chunk_metadata(
                    chunk["metadata"],
                    path.name,
                    file_type,
                    upload_timestamp
                )

            # Step 4: Generate embeddings using OpenAI
            texts = [chunk["text"] for chunk in chunked_documents]
            embeddings = self._generate_embeddings(texts)

            # Step 5: Generate unique IDs
            ids = []
            for idx, chunk in enumerate(chunked_documents):
                chunk_id = self.metadata_extractor.generate_chunk_id(
                    path.name,
                    chunk["metadata"].get("section", ""),
                    idx
                )
                ids.append(chunk_id)

            # Step 6: Store in ChromaDB
            metadatas = [chunk["metadata"] for chunk in chunked_documents]

            chroma_client.add_chunks(
                chunks=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

            return {
                "success": True,
                "file": path.name,
                "file_type": file_type,
                "chunks_created": len(chunked_documents),
                "total_tokens": sum(self.chunker.count_tokens(text) for text in texts),
                "upload_timestamp": upload_timestamp
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file": path.name
            }

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        # OpenAI's embedding model
        model = "text-embedding-3-small"

        # Generate embeddings (batch for efficiency)
        response = self.openai_client.embeddings.create(
            model=model,
            input=texts
        )

        # Extract embeddings from response
        embeddings = [item.embedding for item in response.data]

        return embeddings

    def ingest_multiple_documents(self, file_paths: List[str]) -> Dict:
        """
        Ingest multiple documents

        Args:
            file_paths: List of paths to document files

        Returns:
            Dictionary with aggregated results
        """
        results = []
        for file_path in file_paths:
            result = self.ingest_document(file_path)
            results.append(result)

        # Aggregate statistics
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        return {
            "total_files": len(file_paths),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "total_chunks": sum(r.get("chunks_created", 0) for r in successful)
        }


# Global instance
ingestion_tool = DocumentIngestionTool()
