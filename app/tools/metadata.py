"""
Metadata Query Tool
Provides information about indexed documents and database contents
"""

from typing import List, Dict, Set
from app.db.chroma import chroma_client


class MetadataQueryTool:
    """Tool for querying document metadata and database information"""

    def __init__(self):
        """Initialize the metadata query tool"""
        pass

    def list_indexed_files(self) -> Dict:
        """
        List all files that have been indexed

        Returns:
            Dictionary containing file information
        """
        try:
            collection = chroma_client.get_or_create_collection()
            total_chunks = collection.count()

            if total_chunks == 0:
                return {
                    "success": True,
                    "total_files": 0,
                    "total_chunks": 0,
                    "files": []
                }

            # Get all data from collection (up to a reasonable limit)
            results = collection.get(limit=10000)  # Adjust limit as needed
            metadatas = results.get("metadatas", [])

            # Extract unique filenames
            files_info = {}
            for metadata in metadatas:
                filename = metadata.get("filename", "Unknown")

                if filename not in files_info:
                    files_info[filename] = {
                        "filename": filename,
                        "file_type": metadata.get("file_type", "unknown"),
                        "upload_timestamp": metadata.get("upload_timestamp", "unknown"),
                        "chunk_count": 0
                    }

                files_info[filename]["chunk_count"] += 1

            return {
                "success": True,
                "total_files": len(files_info),
                "total_chunks": total_chunks,
                "files": list(files_info.values())
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_file_info(self, filename: str) -> Dict:
        """
        Get detailed information about a specific file

        Args:
            filename: Name of the file

        Returns:
            Dictionary with file details
        """
        try:
            collection = chroma_client.get_or_create_collection()

            # Query for chunks from this file
            results = collection.get(
                where={"filename": filename},
                limit=10000
            )

            metadatas = results.get("metadatas", [])

            if not metadatas:
                return {
                    "success": False,
                    "error": f"File '{filename}' not found in database"
                }

            # Aggregate information
            sections: Set[str] = set()
            file_type = metadatas[0].get("file_type", "unknown")
            upload_timestamp = metadatas[0].get("upload_timestamp", "unknown")

            for metadata in metadatas:
                section = metadata.get("section", "Unknown")
                sections.add(section)

            return {
                "success": True,
                "filename": filename,
                "file_type": file_type,
                "upload_timestamp": upload_timestamp,
                "chunk_count": len(metadatas),
                "sections": sorted(list(sections))
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the document collection

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = chroma_client.get_or_create_collection()
            total_chunks = collection.count()

            file_info = self.list_indexed_files()

            if not file_info.get("success"):
                return file_info

            # Count by file type
            files = file_info.get("files", [])
            file_types = {}
            for file in files:
                file_type = file.get("file_type", "unknown")
                file_types[file_type] = file_types.get(file_type, 0) + 1

            return {
                "success": True,
                "total_documents": len(files),
                "total_chunks": total_chunks,
                "documents_by_type": file_types,
                "average_chunks_per_document": total_chunks / len(files) if files else 0
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def format_file_list(self, list_result: Dict) -> str:
        """
        Format file list for display

        Args:
            list_result: Result from list_indexed_files()

        Returns:
            Formatted string
        """
        if not list_result.get("success"):
            return f"Error: {list_result.get('error', 'Unknown error')}"

        files = list_result.get("files", [])

        if not files:
            return "No files have been indexed yet."

        lines = [f"Total files indexed: {len(files)}\n"]

        for file in files:
            lines.append(
                f"- {file['filename']} ({file['file_type']}) - "
                f"{file['chunk_count']} chunks - "
                f"Uploaded: {file['upload_timestamp'][:10]}"
            )

        return "\n".join(lines)


# Global instance
metadata_query_tool = MetadataQueryTool()
