"""
Retrieval Tool for Vector Search
Searches the document database for relevant document chunks
"""

import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

from app.db.chroma import chroma_client
from app.ingestion.metadata import MetadataExtractor

load_dotenv()


class RetrievalTool:
    """Tool for retrieving relevant document chunks from the database"""

    def __init__(self):
        """Initialize the retrieval tool"""
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.metadata_extractor = MetadataExtractor()

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Dict = None
    ) -> Dict:
        """
        Retrieve relevant chunks for a query

        Args:
            query: The search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"file_type": "pdf"})

        Returns:
            Dictionary containing:
            - chunks: List of relevant text chunks
            - metadatas: List of metadata for each chunk
            - citations: List of formatted citations
            - distances: Similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = self._generate_query_embedding(query)

            # Search ChromaDB
            results = chroma_client.query_with_embeddings(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )

            # Extract results
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            # Generate citations
            citations = [
                self.metadata_extractor.create_citation(metadata)
                for metadata in metadatas
            ]

            return {
                "success": True,
                "query": query,
                "chunks": documents,
                "metadatas": metadatas,
                "citations": citations,
                "distances": distances,
                "num_results": len(documents)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query using OpenAI

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        model = "text-embedding-3-small"

        response = self.openai_client.embeddings.create(
            model=model,
            input=query
        )

        return response.data[0].embedding

    def format_context_for_agent(self, retrieval_result: Dict) -> str:
        """
        Format retrieval results as context for the agent

        Args:
            retrieval_result: Result from retrieve()

        Returns:
            Formatted context string
        """
        if not retrieval_result.get("success"):
            return "No relevant information found in the database."

        chunks = retrieval_result["chunks"]
        citations = retrieval_result["citations"]

        if not chunks:
            return "No relevant information found in the database."

        # Build formatted context
        context_parts = ["Retrieved information from documents:\n"]

        for idx, (chunk, citation) in enumerate(zip(chunks, citations), 1):
            context_parts.append(f"\n[Source {idx}: {citation}]")
            context_parts.append(chunk)
            context_parts.append("")

        return "\n".join(context_parts)

    def search_by_filename(self, filename: str, n_results: int = 10) -> Dict:
        """
        Retrieve chunks from a specific file

        Args:
            filename: Name of the file to search
            n_results: Number of results to return

        Returns:
            Dictionary with retrieval results
        """
        # Use metadata filter for filename
        filter_metadata = {"filename": filename}

        # Get collection and query without specific search text
        # This will just return chunks from the file
        try:
            results = chroma_client.query(
                query_text="",
                n_results=n_results,
                where=filter_metadata
            )

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            citations = [
                self.metadata_extractor.create_citation(metadata)
                for metadata in metadatas
            ]

            return {
                "success": True,
                "filename": filename,
                "chunks": documents,
                "metadatas": metadatas,
                "citations": citations,
                "num_results": len(documents)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }


# Global instance
retrieval_tool = RetrievalTool()
