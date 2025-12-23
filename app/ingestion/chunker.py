"""
Text Chunking Strategy
Splits documents into appropriately-sized chunks with overlap, respecting structure
"""

from typing import List, Dict
import tiktoken


class TextChunker:
    """
    Chunks text into token-sized pieces with overlap
    Respects document structure to avoid splitting mid-sentence or mid-table
    """

    def __init__(
        self,
        min_chunk_size: int = 300,
        max_chunk_size: int = 600,
        overlap_size: int = 75,
        encoding_name: str = "cl100k_base"  # OpenAI's default encoding
    ):
        """
        Initialize the chunker

        Args:
            min_chunk_size: Minimum tokens per chunk
            max_chunk_size: Maximum tokens per chunk
            overlap_size: Number of tokens to overlap between chunks
            encoding_name: Tiktoken encoding name
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string"""
        return len(self.encoding.encode(text))

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk a single text block into smaller pieces

        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if metadata is None:
            metadata = {}

        token_count = self.count_tokens(text)

        # If text is already small enough, return as single chunk
        if token_count <= self.max_chunk_size:
            return [{
                "text": text,
                "metadata": {**metadata, "chunk_index": 0, "total_chunks": 1}
            }]

        # Split into sentences for structure-aware chunking
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If adding this sentence exceeds max size, finalize current chunk
            if current_tokens + sentence_tokens > self.max_chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {**metadata, "chunk_index": chunk_index}
                })

                # Keep overlap from end of current chunk
                overlap_text = self._get_overlap_text(current_chunk, self.overlap_size)
                current_chunk = [overlap_text] if overlap_text else []
                current_tokens = self.count_tokens(overlap_text) if overlap_text else 0
                chunk_index += 1

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "metadata": {**metadata, "chunk_index": chunk_index}
            })

        # Update total_chunks in all metadata
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = len(chunks)

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving structure

        This is a simple implementation. For production, consider using
        a proper sentence tokenizer like spaCy or NLTK.
        """
        import re

        # Split on common sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Also handle newlines as potential boundaries
        final_sentences = []
        for sentence in sentences:
            if '\n\n' in sentence:
                final_sentences.extend(sentence.split('\n\n'))
            else:
                final_sentences.append(sentence)

        return [s.strip() for s in final_sentences if s.strip()]

    def _get_overlap_text(self, sentences: List[str], overlap_tokens: int) -> str:
        """
        Get the last N tokens worth of sentences for overlap

        Args:
            sentences: List of sentence strings
            overlap_tokens: Number of tokens to include in overlap

        Returns:
            String containing the overlap text
        """
        overlap_sentences = []
        total_tokens = 0

        # Work backwards from end of sentences
        for sentence in reversed(sentences):
            sentence_tokens = self.count_tokens(sentence)
            if total_tokens + sentence_tokens > overlap_tokens:
                break
            overlap_sentences.insert(0, sentence)
            total_tokens += sentence_tokens

        return " ".join(overlap_sentences)

    def chunk_document(self, parsed_chunks: List[Dict]) -> List[Dict]:
        """
        Chunk an entire parsed document

        Args:
            parsed_chunks: List of chunks from document parser
                         Each should have 'text', 'section', and 'metadata' keys

        Returns:
            List of chunked documents with enriched metadata
        """
        all_chunks = []

        for parsed_chunk in parsed_chunks:
            text = parsed_chunk.get("text", "")
            section = parsed_chunk.get("section", "Unknown")
            metadata = parsed_chunk.get("metadata", {})

            # Add section to metadata
            metadata["section"] = section

            # Chunk this parsed section
            text_chunks = self.chunk_text(text, metadata)

            all_chunks.extend(text_chunks)

        return all_chunks
