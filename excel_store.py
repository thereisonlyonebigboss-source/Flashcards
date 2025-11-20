"""
excel_store.py

Handles saving and loading flashcards to/from Excel files.
Supports both global and per-subject storage modes with deduplication.
"""

from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    import pandas as pd

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from config import EXCEL_MODE, GLOBAL_EXCEL_FILENAME, get_excel_filename


# Column names for Excel files
EXCEL_COLUMNS = [
    "Subject",
    "Subtopic",
    "SourceFile",
    "Question",
    "Answer",
    "Difficulty",
    "CreatedAt"
]


def _get_excel_path(output_dir: Path, subject: Optional[str] = None) -> Path:
    """
    Determine the target Excel file path based on storage mode.

    Args:
        output_dir: Directory for storing Excel files
        subject: Subject name (only used in per_subject mode)

    Returns:
        Path object for the target Excel file
    """
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if EXCEL_MODE == "per_subject":
        filename = get_excel_filename(subject)
    else:
        filename = GLOBAL_EXCEL_FILENAME

    return output_dir / filename


def save_records(output_dir: Path, subject: str, records: List[Dict]) -> Path:
    """
    Append flashcard records to the appropriate Excel file.

    Args:
        output_dir: Directory for storing Excel files
        subject: Subject name for the records
        records: List of flashcard records to save

    Returns:
        Path to the saved Excel file
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas library not available. Install with: pip install pandas openpyxl")

    if not records:
        return _get_excel_path(output_dir, subject)

    # Ensure all records have required fields and proper formatting
    formatted_records = []
    for record in records:
        formatted_record = {
            "Subject": str(record.get("Subject", "")),
            "Subtopic": str(record.get("Subtopic", "")),
            "SourceFile": str(record.get("SourceFile", "")),
            "Question": str(record.get("Question", "")),
            "Answer": str(record.get("Answer", "")),
            "Difficulty": str(record.get("Difficulty", "")),
            "CreatedAt": record.get("CreatedAt", datetime.now().isoformat())
        }
        formatted_records.append(formatted_record)

    excel_path = _get_excel_path(output_dir, subject)
    df_new = pd.DataFrame(formatted_records)

    try:
        if excel_path.exists():
            # Load existing data and append
            df_old = pd.read_excel(excel_path)
            df = pd.concat([df_old, df_new], ignore_index=True)

            # Remove duplicates based on question, answer, subject, and subtopic
            df = df.drop_duplicates(
                subset=["Question", "Answer", "Subject", "Subtopic"],
                keep="last"
            )
        else:
            # Create new DataFrame with proper column order
            df = df_new

        # Ensure all columns exist in the correct order
        for col in EXCEL_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        df = df[EXCEL_COLUMNS]  # Reorder columns

        # Save to Excel
        df.to_excel(excel_path, index=False, engine="openpyxl")

    except Exception as e:
        print(f"[ERROR] Failed to save Excel file {excel_path}: {e}")
        raise

    return excel_path


def load_all_records(output_dir: Path):
    """
    Load all flashcards from Excel files in output_dir.

    Args:
        output_dir: Directory containing Excel flashcard files

    Returns:
        DataFrame containing all flashcard records
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas library not available. Install with: pip install pandas openpyxl")

    output_dir = output_dir.resolve()

    if not output_dir.exists():
        return pd.DataFrame(columns=EXCEL_COLUMNS)

    excel_files = list(output_dir.glob("*.xlsx"))
    if not excel_files:
        return pd.DataFrame(columns=EXCEL_COLUMNS)

    dfs = []
    for excel_file in excel_files:
        try:
            df = pd.read_excel(excel_file)

            # Ensure required columns exist
            for col in EXCEL_COLUMNS:
                if col not in df.columns:
                    df[col] = ""

            # Reorder columns to match standard
            df = df[EXCEL_COLUMNS]
            dfs.append(df)

        except Exception as e:
            print(f"[WARN] Failed to read {excel_file.name}: {e}")
            continue

    if not dfs:
        return pd.DataFrame(columns=EXCEL_COLUMNS)

    # Concatenate all DataFrames and remove any final duplicates
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df = combined_df.drop_duplicates(
        subset=["Question", "Answer", "Subject", "Subtopic"],
        keep="last"
    )

    return combined_df


def get_available_subjects(output_dir: Path) -> List[str]:
    """
    Get list of available subjects from Excel files.

    Args:
        output_dir: Directory containing Excel flashcard files

    Returns:
        Sorted list of unique subject names
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas library not available. Install with: pip install pandas openpyxl")

    df = load_all_records(output_dir)
    if df.empty:
        return []

    subjects = df["Subject"].dropna().unique().tolist()
    return sorted([str(s) for s in subjects if s.strip()])


def get_available_subtopics(output_dir: Path, subject: Optional[str] = None) -> List[str]:
    """
    Get list of available subtopics, optionally filtered by subject.

    Args:
        output_dir: Directory containing Excel flashcard files
        subject: Optional subject filter

    Returns:
        Sorted list of unique subtopic names
    """
    df = load_all_records(output_dir)
    if df.empty:
        return []

    if subject:
        df = df[df["Subject"] == subject]

    subtopics = df["Subtopic"].dropna().unique().tolist()
    return sorted([str(s) for s in subtopics if s.strip()])


def get_flashcard_count(output_dir: Path, subject: Optional[str] = None, subtopic: Optional[str] = None) -> int:
    """
    Get count of flashcards, optionally filtered by subject and/or subtopic.

    Args:
        output_dir: Directory containing Excel flashcard files
        subject: Optional subject filter
        subtopic: Optional subtopic filter

    Returns:
        Number of matching flashcards
    """
    df = load_all_records(output_dir)
    if df.empty:
        return 0

    if subject:
        df = df[df["Subject"] == subject]

    if subtopic:
        df = df[df["Subtopic"] == subtopic]

    return len(df)


def backup_excel_file(file_path: Path) -> Path:
    """
    Create a backup of an Excel file before modifications.

    Args:
        file_path: Path to the Excel file to backup

    Returns:
        Path to the backup file
    """
    if not file_path.exists():
        return file_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"

    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"[INFO] Created backup: {backup_path}")
    except Exception as e:
        print(f"[WARN] Failed to create backup of {file_path}: {e}")

    return backup_path