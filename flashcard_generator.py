"""
flashcard_generator.py

Coordinates the complete flashcard generation pipeline:
text extraction -> chunking -> AI processing -> metadata attachment -> Excel storage.
"""

from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from config import MAX_CHARS_PER_CHUNK, DEFAULT_CARDS_PER_CHUNK
from text_extraction import extract_text
from ai_client import FlashcardAIClient


def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> List[str]:
    """
    Split text into chunks while preserving sentence boundaries.

    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    chunks = []
    current_chunk = ""
    sentences = []

    # Split into sentences (simple approach - split on period, question mark, exclamation)
    import re
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If adding this sentence would exceed the limit, start a new chunk
        if len(current_chunk) + len(sentence) + 1 > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

    # Add the last chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # If no sentences were found, fall back to character-based chunking
    if not chunks:
        return _fallback_chunking(text, max_chars)

    return chunks


def _fallback_chunking(text: str, max_chars: int) -> List[str]:
    """
    Fallback chunking method that splits on paragraphs or lines.

    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    chunks = []
    current_lines = []
    current_len = 0

    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            # Add empty lines as paragraph breaks
            if current_lines:
                chunks.append("\n".join(current_lines))
                current_lines = []
                current_len = 0
            continue

        line_len = len(line) + 1  # +1 for newline

        if current_len + line_len > max_chars and current_lines:
            chunks.append("\n".join(current_lines))
            current_lines = [line]
            current_len = line_len
        else:
            current_lines.append(line)
            current_len += line_len

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks


def generate_flashcards_for_file(
    ai_client: FlashcardAIClient,
    file_info: Dict,
    cards_per_chunk: int = DEFAULT_CARDS_PER_CHUNK,
    min_chunk_size: int = 100
) -> List[Dict]:
    """
    Generate flashcards from a single file.

    Args:
        ai_client: AI client for flashcard generation
        file_info: Dictionary containing file metadata
        cards_per_chunk: Number of flashcards to generate per chunk
        min_chunk_size: Minimum character count for a chunk to be processed

    Returns:
        List of flashcard records with metadata
    """
    path: Path = file_info["full_path"]
    subject: str = file_info["subject"]
    subtopic: str = file_info["subtopic"]
    filename: str = file_info["filename"]

    try:
        print(f"  Extracting text from {filename}...")
        raw_text = extract_text(path)

        if not raw_text or len(raw_text.strip()) < min_chunk_size:
            print(f"  Skipping {filename}: insufficient text content ({len(raw_text)} chars)")
            return []

        print(f"  Text extracted ({len(raw_text)} chars). Chunking...")
        chunks = chunk_text(raw_text)
        print(f"  Created {len(chunks)} chunks")

        all_records = []
        successful_chunks = 0

        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip() or len(chunk.strip()) < min_chunk_size:
                continue

            print(f"  Processing chunk {i}/{len(chunks)} ({len(chunk)} chars)...")

            try:
                cards = ai_client.generate_flashcards_from_text(
                    chunk,
                    num_cards=cards_per_chunk
                )

                if cards:
                    for card in cards:
                        record = {
                            "Subject": subject,
                            "Subtopic": subtopic,
                            "SourceFile": filename,
                            "Question": card["question"],
                            "Answer": card["answer"],
                            "Difficulty": "",  # Empty for v1
                            "CreatedAt": datetime.now().isoformat()
                        }
                        all_records.append(record)

                    successful_chunks += 1
                    print(f"    Generated {len(cards)} flashcards")
                else:
                    print(f"    No flashcards generated for chunk {i}")

            except Exception as e:
                print(f"    Failed to process chunk {i}: {e}")
                continue

        print(f"  Completed {filename}: {len(all_records)} flashcards from {successful_chunks} chunks")
        return all_records

    except Exception as e:
        print(f"  Failed to process {filename}: {e}")
        return []


def generate_flashcards_for_files(
    ai_client: FlashcardAIClient,
    files_info: List[Dict],
    cards_per_chunk: int = DEFAULT_CARDS_PER_CHUNK,
    progress_callback: Optional[callable] = None
) -> Dict[str, List[Dict]]:
    """
    Generate flashcards from multiple files.

    Args:
        ai_client: AI client for flashcard generation
        files_info: List of file metadata dictionaries
        cards_per_chunk: Number of flashcards to generate per chunk
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary mapping filenames to their flashcard records
    """
    results = {}
    total_files = len(files_info)
    processed_files = 0

    for i, file_info in enumerate(files_info, 1):
        filename = file_info["filename"]

        if progress_callback:
            progress_callback(i, total_files, filename)

        try:
            records = generate_flashcards_for_file(
                ai_client,
                file_info,
                cards_per_chunk
            )

            if records:
                results[filename] = records
                processed_files += 1

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    print(f"\nGeneration complete: {processed_files}/{total_files} files processed")
    print(f"Total flashcards generated: {sum(len(records) for records in results.values())}")

    return results


def validate_flashcard_record(record: Dict) -> bool:
    """
    Validate that a flashcard record has all required fields.

    Args:
        record: Flashcard record to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["Subject", "Subtopic", "SourceFile", "Question", "Answer"]

    for field in required_fields:
        if field not in record or not record[field] or not str(record[field]).strip():
            return False

    # Additional validation
    question = str(record["Question"]).strip()
    answer = str(record["Answer"]).strip()

    if len(question) < 10 or len(answer) < 5:
        return False

    # Check for extremely long fields that might indicate errors
    if len(question) > 1000 or len(answer) > 2000:
        return False

    return True


def filter_duplicate_questions(records: List[Dict]) -> List[Dict]:
    """
    Remove duplicate questions from a list of flashcard records.

    Args:
        records: List of flashcard records

    Returns:
        Filtered list with duplicates removed
    """
    seen_questions = set()
    filtered_records = []

    for record in records:
        question = str(record["Question"]).strip().lower()
        if question not in seen_questions:
            seen_questions.add(question)
            filtered_records.append(record)

    return filtered_records


def get_generation_statistics(results: Dict[str, List[Dict]]) -> Dict:
    """
    Calculate statistics about the generation process.

    Args:
        results: Dictionary mapping filenames to flashcard records

    Returns:
        Dictionary with generation statistics
    """
    total_records = sum(len(records) for records in results.values())
    files_processed = len(results)
    questions_by_subject = {}
    questions_by_file = {}

    for filename, records in results.items():
        questions_by_file[filename] = len(records)

        for record in records:
            subject = str(record["Subject"])
            questions_by_subject[subject] = questions_by_subject.get(subject, 0) + 1

    return {
        "total_flashcards": total_records,
        "files_processed": files_processed,
        "questions_by_subject": questions_by_subject,
        "questions_by_file": questions_by_file,
        "average_cards_per_file": total_records / files_processed if files_processed > 0 else 0
    }