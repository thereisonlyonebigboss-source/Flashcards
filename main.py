"""
main.py

CLI entry point for the Flashcard Generator application.
Provides menu system for generating flashcards and taking quizzes.
"""

import sys
from pathlib import Path
from typing import Optional

from config import resolve_path, DEFAULT_CARDS_PER_CHUNK, EXCEL_MODE, GLOBAL_EXCEL_FILENAME
from text_extraction import iter_note_files, get_supported_extensions
from flashcard_generator import generate_flashcards_for_files, get_generation_statistics
from excel_store import save_records, load_all_records, backup_excel_file, PANDAS_AVAILABLE
from ai_client import create_ai_client, FlashcardAIClient
from quiz_cli import main_quiz_interface


def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("  Local AI Flashcard Generator & Quiz Tool")
    print("  Powered by Llama 2")
    print("=" * 60)
    print()


def print_menu():
    """Print main menu options."""
    print("Main Menu:")
    print("1. Generate flashcards from notes")
    print("2. Quiz myself")
    print("3. View statistics")
    print("4. Configuration info")
    print("5. Exit")


def get_path_input(prompt: str, must_exist: bool = True) -> Optional[Path]:
    """
    Get and validate a path from user input.

    Args:
        prompt: Prompt message for user
        must_exist: Whether the path must exist

    Returns:
        Validated Path object or None if user cancels
    """
    while True:
        try:
            path_str = input(prompt).strip()
            if not path_str:
                print("No path entered. Please try again.")
                continue

            path = resolve_path(path_str)

            if must_exist and not path.exists():
                print(f"Path does not exist: {path}")
                continue

            if must_exist and not path.is_dir():
                print(f"Path is not a directory: {path}")
                continue

            return path

        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return None
        except Exception as e:
            print(f"Invalid path: {e}")
            continue


def get_number_input(prompt: str, default: Optional[int] = None, min_val: Optional[int] = None) -> int:
    """
    Get a number from user input with validation.

    Args:
        prompt: Prompt message for user
        default: Default value if user enters empty string
        min_val: Minimum allowed value

    Returns:
        Validated integer
    """
    while True:
        try:
            input_str = input(prompt).strip()

            if not input_str and default is not None:
                print(f"Using default: {default}")
                return default

            if not input_str:
                print("Please enter a number.")
                continue

            value = int(input_str)

            if min_val is not None and value < min_val:
                print(f"Please enter a number greater than or equal to {min_val}.")
                continue

            return value

        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            raise
        except ValueError:
            print("Please enter a valid number.")
            continue


def get_ai_backend_choice() -> tuple:
    """
    Let user choose AI backend and configuration.

    Returns:
        Tuple of (backend_type, backend_config)
    """
    print("\nAI Backend Selection:")
    print("1. HuggingFace Transformers (local Llama 2)")
    print("2. Ollama (local Ollama server)")
    print("3. HTTP API (custom endpoint)")

    while True:
        try:
            choice = input("Select AI backend (1-3): ").strip()

            if choice == "1":
                # Transformers configuration
                model_name = input("Model name (press Enter for default): ").strip()
                if not model_name:
                    model_name = "meta-llama/Llama-2-7b-chat-hf"

                device_choice = input("Device (cpu/cuda, default: cpu): ").strip().lower()
                device = "cuda" if device_choice == "cuda" else "cpu"

                return "transformers", {"model_name": model_name, "device": device}

            elif choice == "2":
                # Ollama configuration
                model_name = input("Ollama model name (default: llama2): ").strip()
                if not model_name:
                    model_name = "llama2"

                base_url = input("Ollama base URL (default: http://localhost:11434): ").strip()
                if not base_url:
                    base_url = "http://localhost:11434"

                return "ollama", {"model_name": model_name, "base_url": base_url}

            elif choice == "3":
                # HTTP API configuration
                api_url = input("API endpoint URL: ").strip()
                if not api_url:
                    print("API URL is required for HTTP backend.")
                    continue

                return "http", {"api_url": api_url}

            else:
                print("Please enter 1, 2, or 3.")

        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            raise
        except Exception as e:
            print(f"Error configuring backend: {e}")


def cmd_generate():
    """Handle flashcard generation command."""
    print("\n" + "=" * 60)
    print("GENERATE FLASHCARDS")
    print("=" * 60)

    # Get paths
    root_path = get_path_input("Enter path to root notes folder: ", must_exist=True)
    if root_path is None:
        return

    output_path = get_path_input("Enter path to output folder: ", must_exist=False)
    if output_path is None:
        return

    # Create output directory if it doesn't exist
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory: {e}")
        return

    # Get generation parameters
    try:
        cards_per_chunk = get_number_input(
            f"Cards per chunk (default: {DEFAULT_CARDS_PER_CHUNK}): ",
            default=DEFAULT_CARDS_PER_CHUNK,
            min_val=1
        )
    except KeyboardInterrupt:
        return

    # Scan for files
    print(f"\nScanning for supported files in: {root_path}")
    supported_extensions = get_supported_extensions()
    print(f"Supported file types: {', '.join(sorted(supported_extensions))}")

    files_info = list(iter_note_files(root_path))

    if not files_info:
        print("No supported files found in the specified directory.")
        return

    print(f"Found {len(files_info)} supported files:")
    subjects = {}
    for file_info in files_info:
        subject = file_info["subject"]
        subjects[subject] = subjects.get(subject, 0) + 1

    for subject, count in sorted(subjects.items()):
        print(f"  {subject}: {count} files")

    # Get AI backend configuration
    try:
        backend_type, backend_config = get_ai_backend_choice()
    except KeyboardInterrupt:
        return

    # Initialize AI client
    try:
        print(f"\nInitializing AI client ({backend_type})...")
        ai_client = create_ai_client(backend_type, **backend_config)
        print("AI client initialized successfully.")
    except Exception as e:
        print(f"Error initializing AI client: {e}")
        print("Please check your AI backend configuration and try again.")
        return

    # Generate flashcards
    try:
        print(f"\nGenerating flashcards...")
        print(f"Configuration: {cards_per_chunk} cards per chunk")

        def progress_callback(current, total, filename):
            print(f"[{current}/{total}] Processing {filename}...")

        results = generate_flashcards_for_files(
            ai_client,
            files_info,
            cards_per_chunk=cards_per_chunk,
            progress_callback=progress_callback
        )

        if not results:
            print("No flashcards were generated.")
            return

        # Save to Excel
        print("\nSaving flashcards to Excel files...")
        total_saved = 0
        saved_files = []

        for subject in subjects.keys():
            # Collect all records for this subject
            subject_records = []
            for filename, records in results.items():
                for record in records:
                    if record["Subject"] == subject:
                        subject_records.append(record)

            if subject_records:
                try:
                    excel_path = save_records(output_path, subject, subject_records)
                    saved_files.append(excel_path)
                    total_saved += len(subject_records)
                    print(f"  {subject}: {len(subject_records)} cards -> {excel_path.name}")
                except Exception as e:
                    print(f"  Error saving {subject}: {e}")

        # Display statistics
        stats = get_generation_statistics(results)
        print(f"\n" + "=" * 60)
        print("GENERATION COMPLETE")
        print("=" * 60)
        print(f"Total flashcards generated: {stats['total_flashcards']}")
        print(f"Files processed: {stats['files_processed']}/{len(files_info)}")
        print(f"Excel files created: {len(saved_files)}")
        print(f"Average cards per file: {stats['average_cards_per_file']:.1f}")

        if saved_files:
            print(f"\nFlashcards saved to: {output_path}")
            for file_path in saved_files:
                print(f"  - {file_path.name}")

    except KeyboardInterrupt:
        print("\nGeneration cancelled by user.")
    except Exception as e:
        print(f"\nError during generation: {e}")

    input("\nPress Enter to return to main menu...")


def cmd_quiz():
    """Handle quiz command."""
    print("\n" + "=" * 60)
    print("QUIZ MODE")
    print("=" * 60)

    output_path = get_path_input("Enter path to flashcards output folder: ", must_exist=True)
    if output_path is None:
        return

    try:
        main_quiz_interface(output_path)
    except Exception as e:
        print(f"Error in quiz interface: {e}")
        input("Press Enter to return to main menu...")


def cmd_statistics():
    """Handle statistics command."""
    print("\n" + "=" * 60)
    print("FLASHCARD STATISTICS")
    print("=" * 60)

    output_path = get_path_input("Enter path to flashcards output folder: ", must_exist=True)
    if output_path is None:
        return

    try:
        df = load_all_records(output_path)

        if df.empty:
            print("No flashcards found.")
            input("Press Enter to return to main menu...")
            return

        print(f"Total flashcards: {len(df)}")

        # Statistics by subject
        subjects = df['Subject'].value_counts()
        print(f"\nBy Subject ({len(subjects)} subjects):")
        for subject, count in subjects.head(10).items():
            print(f"  {subject}: {count} cards")
        if len(subjects) > 10:
            print(f"  ... and {len(subjects) - 10} more subjects")

        # Statistics by subtopic
        subtopics = df['Subtopic'].value_counts()
        print(f"\nBy Subtopic ({len(subtopics)} subtopics):")
        for subtopic, count in subtopics.head(10).items():
            print(f"  {subtopic}: {count} cards")
        if len(subtopics) > 10:
            print(f"  ... and {len(subtopics) - 10} more subtopics")

        # File statistics
        files = df['SourceFile'].value_counts()
        print(f"\nBy Source File ({len(files)} files):")
        for filename, count in files.head(10).items():
            print(f"  {filename}: {count} cards")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more files")

        # Excel files
        excel_files = list(output_path.glob("*.xlsx"))
        print(f"\nExcel files: {len(excel_files)}")
        for excel_file in excel_files:
            print(f"  - {excel_file.name}")

    except Exception as e:
        print(f"Error loading statistics: {e}")

    input("\nPress Enter to return to main menu...")


def cmd_config_info():
    """Display configuration information."""
    print("\n" + "=" * 60)
    print("CONFIGURATION INFORMATION")
    print("=" * 60)

    print(f"Current configuration:")
    print(f"  Excel mode: {EXCEL_MODE}")
    if EXCEL_MODE == "global":
        print(f"  Global Excel file: {GLOBAL_EXCEL_FILENAME}")
    print(f"  Max characters per chunk: {2000}")
    print(f"  Default cards per chunk: {DEFAULT_CARDS_PER_CHUNK}")
    print(f"\nSupported file formats:")
    for ext in sorted(get_supported_extensions()):
        print(f"  - {ext}")

    print(f"\nSupported AI backends:")
    print(f"  1. HuggingFace Transformers (local models)")
    print(f"  2. Ollama (local server)")
    print(f"  3. HTTP API (custom endpoints)")

    input("\nPress Enter to return to main menu...")


def main():
    """Main application loop."""
    try:
        while True:
            print_banner()
            print_menu()

            try:
                choice = input("Enter your choice (1-5): ").strip()

                if choice == "1":
                    cmd_generate()
                elif choice == "2":
                    cmd_quiz()
                elif choice == "3":
                    cmd_statistics()
                elif choice == "4":
                    cmd_config_info()
                elif choice == "5":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please enter 1-5.")
                    input("Press Enter to continue...")

            except KeyboardInterrupt:
                print("\nReturning to main menu...")
                continue
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")

    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()