"""
config.py

Configuration management for the flashcard generator application.
Centralized settings for text processing, AI integration, and Excel storage.
"""

from pathlib import Path

# Text processing configuration
MAX_CHARS_PER_CHUNK = 2000
DEFAULT_CARDS_PER_CHUNK = 8

# Excel storage configuration
EXCEL_MODE = "global"  # "global" or "per_subject"
GLOBAL_EXCEL_FILENAME = "flashcards.xlsx"

# AI model configuration
DEFAULT_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_NEW_TOKENS = 1024


def resolve_path(path_str: str) -> Path:
    """
    Convert a path string to a resolved absolute Path object.

    Args:
        path_str: Path string to resolve

    Returns:
        Resolved absolute Path object
    """
    return Path(path_str).expanduser().resolve()


def get_excel_filename(subject: str = None) -> str:
    """
    Get the appropriate Excel filename based on the storage mode.

    Args:
        subject: Subject name (only used in per_subject mode)

    Returns:
        Excel filename
    """
    if EXCEL_MODE == "per_subject":
        if subject:
            return f"{subject}_flashcards.xlsx"
        return "General_flashcards.xlsx"
    return GLOBAL_EXCEL_FILENAME