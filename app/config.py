"""
Configuration Management for LLM and Embedding Providers
Supports both OpenAI and Ollama providers
"""

import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for the application"""

    # LLM Provider: "openai" or "ollama"
    LLM_PROVIDER: Literal["openai", "ollama"] = os.getenv("LLM_PROVIDER", "openai")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    # Database Configuration
    CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./data/chroma")
    UPLOAD_PATH: str = os.getenv("UPLOAD_PATH", "./data/raw_uploads")

    @classmethod
    def validate(cls) -> tuple[bool, str]:
        """
        Validate configuration based on selected provider

        Returns:
            Tuple of (is_valid, error_message)
        """
        if cls.LLM_PROVIDER == "openai":
            if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == "your-openai-api-key-here":
                return False, "OpenAI API key is required when using LLM_PROVIDER=openai"
        elif cls.LLM_PROVIDER == "ollama":
            # For Ollama, we just need the base URL to be set
            if not cls.OLLAMA_BASE_URL:
                return False, "OLLAMA_BASE_URL is required when using LLM_PROVIDER=ollama"
        else:
            return False, f"Invalid LLM_PROVIDER: {cls.LLM_PROVIDER}. Must be 'openai' or 'ollama'"

        return True, ""

    @classmethod
    def get_embedding_config(cls) -> dict:
        """Get embedding configuration based on provider"""
        if cls.LLM_PROVIDER == "openai":
            return {
                "provider": "openai",
                "api_key": cls.OPENAI_API_KEY,
                "model": cls.OPENAI_EMBEDDING_MODEL
            }
        else:  # ollama
            return {
                "provider": "ollama",
                "base_url": cls.OLLAMA_BASE_URL,
                "model": cls.OLLAMA_EMBEDDING_MODEL
            }

    @classmethod
    def get_llm_config(cls) -> dict:
        """Get LLM configuration based on provider"""
        if cls.LLM_PROVIDER == "openai":
            return {
                "provider": "openai",
                "api_key": cls.OPENAI_API_KEY,
                "model": cls.OPENAI_MODEL
            }
        else:  # ollama
            return {
                "provider": "ollama",
                "base_url": cls.OLLAMA_BASE_URL,
                "model": cls.OLLAMA_MODEL
            }


# Global config instance
config = Config()
