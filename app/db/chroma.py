"""
ChromaDB Vector Database Interface
Handles initialization, persistence, and operations for the local vector store
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()


class ChromaDBClient:
    """Singleton client for ChromaDB operations"""

    _instance = None
    _client = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client with persistent storage"""
        chroma_path = Path(os.getenv("CHROMA_PATH", "./data/chroma"))
        chroma_path.mkdir(parents=True, exist_ok=True)

        # Create ChromaDB client with persistent storage
        self._client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    def get_or_create_collection(self, collection_name: str = "eln_documents"):
        """
        Get or create a ChromaDB collection for ELN documents

        Args:
            collection_name: Name of the collection

        Returns:
            ChromaDB collection object
        """
        if self._collection is None or self._collection.name != collection_name:
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Electronic Lab Notebook documents and chunks"}
            )
        return self._collection

    def add_chunks(
        self,
        chunks: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Add document chunks to the collection

        Args:
            chunks: List of text chunks
            metadatas: List of metadata dictionaries for each chunk
            ids: List of unique IDs for each chunk
            embeddings: Optional pre-computed embeddings (if None, ChromaDB will compute them)
        """
        collection = self.get_or_create_collection()

        if embeddings:
            collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
        else:
            # Let ChromaDB compute embeddings using its default embedding function
            collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the collection for similar chunks

        Args:
            query_text: The query string
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Dictionary with query results including documents, metadatas, and distances
        """
        collection = self.get_or_create_collection()

        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )

        return results

    def query_with_embeddings(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the collection using pre-computed embeddings

        Args:
            query_embeddings: Pre-computed query embeddings
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Dictionary with query results
        """
        collection = self.get_or_create_collection()

        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

        return results

    def get_collection_count(self) -> int:
        """Get the number of documents in the collection"""
        collection = self.get_or_create_collection()
        return collection.count()

    def delete_collection(self, collection_name: str = "eln_documents"):
        """Delete a collection"""
        try:
            self._client.delete_collection(name=collection_name)
            self._collection = None
        except Exception as e:
            print(f"Error deleting collection: {e}")

    def reset(self):
        """Reset the ChromaDB client and delete all collections"""
        self._client.reset()
        self._collection = None


# Global instance
chroma_client = ChromaDBClient()
