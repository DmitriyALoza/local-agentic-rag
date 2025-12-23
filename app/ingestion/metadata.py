"""
Metadata Extraction and Enrichment
Utilities for handling document and chunk metadata
"""

from datetime import datetime
from typing import Dict, List
from pathlib import Path


class MetadataExtractor:
    """Extracts and enriches metadata for documents and chunks"""

    @staticmethod
    def enrich_chunk_metadata(
        metadata: Dict,
        filename: str,
        file_type: str,
        upload_timestamp: str = None
    ) -> Dict:
        """
        Enrich chunk metadata with standard fields

        Args:
            metadata: Existing metadata dictionary
            filename: Name of the source file
            file_type: Type of file (pdf, pptx, docx, xlsx)
            upload_timestamp: ISO format timestamp of upload

        Returns:
            Enriched metadata dictionary
        """
        enriched = metadata.copy()

        # Add standard fields
        enriched["filename"] = filename
        enriched["file_type"] = file_type

        if upload_timestamp is None:
            upload_timestamp = datetime.now().isoformat()

        enriched["upload_timestamp"] = upload_timestamp

        # Add chunk ID components
        if "section" not in enriched:
            enriched["section"] = "Unknown"

        return enriched

    @staticmethod
    def generate_chunk_id(
        filename: str,
        section: str,
        chunk_index: int = 0
    ) -> str:
        """
        Generate a unique ID for a chunk

        Args:
            filename: Name of the source file
            section: Section identifier
            chunk_index: Index of this chunk within the section

        Returns:
            Unique chunk ID string
        """
        # Clean filename and section for use in ID
        clean_filename = Path(filename).stem.replace(" ", "_")
        clean_section = section.replace(" ", "_").replace(":", "_")

        return f"{clean_filename}__{clean_section}__chunk_{chunk_index}"

    @staticmethod
    def create_citation(metadata: Dict) -> str:
        """
        Create a human-readable citation from metadata

        Args:
            metadata: Chunk metadata

        Returns:
            Citation string
        """
        filename = metadata.get("filename", "Unknown file")
        section = metadata.get("section", "Unknown section")

        # Add page/slide number if available
        if "page_number" in metadata:
            return f"{filename}, Page {metadata['page_number']}"
        elif "slide_number" in metadata:
            return f"{filename}, Slide {metadata['slide_number']}"
        elif "sheet_name" in metadata:
            return f"{filename}, Sheet: {metadata['sheet_name']}"
        else:
            return f"{filename}, {section}"

    @staticmethod
    def extract_file_info(file_path: str) -> Dict:
        """
        Extract basic file information

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information
        """
        path = Path(file_path)

        return {
            "filename": path.name,
            "file_type": path.suffix.lstrip('.').lower(),
            "file_size_bytes": path.stat().st_size,
            "upload_timestamp": datetime.now().isoformat()
        }
