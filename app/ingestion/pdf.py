"""
PDF Document Parser
Extracts text from PDF files with OCR fallback capability
"""

from pathlib import Path
from typing import List, Dict
from pypdf import PdfReader


class PDFParser:
    """Parser for PDF files"""

    def parse(self, file_path: str) -> List[Dict]:
        """
        Parse a PDF file and extract structured content

        Args:
            file_path: Path to the .pdf file

        Returns:
            List of dictionaries, each containing:
            - text: The extracted text content
            - section: Section identifier (page number)
            - metadata: Additional metadata about the content
        """
        reader = PdfReader(file_path)
        chunks = []
        filename = Path(file_path).name

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                # Extract text from page
                text = page.extract_text()

                if text and text.strip():
                    chunks.append({
                        "text": text.strip(),
                        "section": f"Page {page_num}",
                        "metadata": {
                            "filename": filename,
                            "page_number": page_num,
                            "content_type": "page",
                            "extraction_method": "text"
                        }
                    })
                else:
                    # Page has no extractable text - could be image-based
                    chunks.append({
                        "text": f"[Page {page_num} contains no extractable text - may be image-based]",
                        "section": f"Page {page_num} (No Text)",
                        "metadata": {
                            "filename": filename,
                            "page_number": page_num,
                            "content_type": "image_page",
                            "extraction_method": "none",
                            "note": "OCR may be needed for this page"
                        }
                    })

            except Exception as e:
                # Error extracting from this page
                chunks.append({
                    "text": f"[Error extracting text from page {page_num}: {str(e)}]",
                    "section": f"Page {page_num} (Error)",
                    "metadata": {
                        "filename": filename,
                        "page_number": page_num,
                        "content_type": "error",
                        "error": str(e)
                    }
                })

        return chunks

    def get_metadata(self, file_path: str) -> Dict:
        """
        Get metadata about the PDF file

        Args:
            file_path: Path to the .pdf file

        Returns:
            Dictionary containing file metadata
        """
        reader = PdfReader(file_path)
        path = Path(file_path)

        # Extract PDF metadata
        pdf_metadata = {}
        if reader.metadata:
            pdf_metadata = {
                "author": reader.metadata.get("/Author", "Unknown"),
                "title": reader.metadata.get("/Title", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "creator": reader.metadata.get("/Creator", ""),
                "producer": reader.metadata.get("/Producer", ""),
            }

        return {
            "filename": path.name,
            "file_type": "pdf",
            "total_pages": len(reader.pages),
            "file_size_bytes": path.stat().st_size,
            "pdf_metadata": pdf_metadata
        }
