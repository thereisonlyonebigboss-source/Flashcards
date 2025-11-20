"""
quiz_cli.py

Terminal-based quiz interface with filtering, scoring, and review features.
Provides an interactive flashcard testing experience.
"""

from typing import Optional, List, Dict, TYPE_CHECKING
import random
import sys

if TYPE_CHECKING:
    import pandas as pd

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from excel_store import load_all_records, get_available_subjects, get_available_subtopics


def clear_screen():
    """Clear the terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    """Print a formatted header."""
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)


def wait_for_enter(message: str = "Press Enter to continue..."):
    """Wait for user to press Enter."""
    input(f"\n{message}")


def select_subject(df) -> Optional:
    """
    Let user select a subject from available options.

    Args:
        df: DataFrame of all flashcards

    Returns:
        Filtered DataFrame or None if user wants to go back
    """
    if df.empty:
        print("No flashcards available.")
        return None

    subjects = sorted(df["Subject"].dropna().unique().tolist())

    print_header("SELECT SUBJECT")
    print("Available subjects:")
    for i, subject in enumerate(subjects, start=1):
        count = len(df[df["Subject"] == subject])
        print(f"{i:2d}. {subject} ({count} cards)")
    print(f"{len(subjects) + 1:2d}. ALL SUBJECTS ({len(df)} cards)")
    print(" 0. Back to main menu")

    while True:
        try:
            choice = input("\nSelect subject number: ").strip()

            if choice == "0":
                return None

            choice_num = int(choice)

            if 1 <= choice_num <= len(subjects):
                subject = subjects[choice_num - 1]
                filtered_df = df[df["Subject"] == subject].copy()
                print(f"\nSelected: {subject} ({len(filtered_df)} cards)")
                wait_for_enter()
                return filtered_df
            elif choice_num == len(subjects) + 1:
                print(f"\nSelected: ALL SUBJECTS ({len(df)} cards)")
                wait_for_enter()
                return df.copy()
            else:
                print("Invalid choice. Please try again.")

        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            return None


def select_subtopic(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Let user select a subtopic from available options.

    Args:
        df: DataFrame of flashcards (already filtered by subject)

    Returns:
        Filtered DataFrame or None if user wants to go back
    """
    if df.empty:
        print("No flashcards available.")
        return None

    subtopics = sorted(df["Subtopic"].dropna().unique().tolist())

    print_header("SELECT SUBTOPIC")

    # Show current subject if there's only one
    subjects = df["Subject"].dropna().unique().tolist()
    if len(subjects) == 1:
        print(f"Subject: {subjects[0]}")

    print("Available subtopics:")
    for i, subtopic in enumerate(subtopics, start=1):
        count = len(df[df["Subtopic"] == subtopic])
        print(f"{i:2d}. {subtopic} ({count} cards)")
    print(f"{len(subtopics) + 1:2d}. ALL SUBTOPICS ({len(df)} cards)")
    print(" 0. Back to subject selection")

    while True:
        try:
            choice = input("\nSelect subtopic number: ").strip()

            if choice == "0":
                return None

            choice_num = int(choice)

            if 1 <= choice_num <= len(subtopics):
                subtopic = subtopics[choice_num - 1]
                filtered_df = df[df["Subtopic"] == subtopic].copy()
                print(f"\nSelected: {subtopic} ({len(filtered_df)} cards)")
                wait_for_enter()
                return filtered_df
            elif choice_num == len(subtopics) + 1:
                print(f"\nSelected: ALL SUBTOPICS ({len(df)} cards)")
                wait_for_enter()
                return df.copy()
            else:
                print("Invalid choice. Please try again.")

        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nReturning to subject selection...")
            return None


def select_question_limit() -> Optional[int]:
    """
    Let user select the maximum number of questions.

    Returns:
        Question limit or None for all questions
    """
    print_header("QUESTION LIMIT")
    print("How many questions would you like to answer?")
    print("Leave blank to answer all available questions")
    print("Enter 0 to go back to subtopic selection")

    while True:
        try:
            choice = input("\nNumber of questions (or press Enter for all): ").strip()

            if choice == "0":
                return None
            elif not choice:
                print("Will ask all available questions")
                wait_for_enter()
                return None
            else:
                limit = int(choice)
                if limit > 0:
                    print(f"Will ask up to {limit} questions")
                    wait_for_enter()
                    return limit
                else:
                    print("Please enter a positive number.")

        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nReturning to subtopic selection...")
            return None


def display_question(card: Dict, question_num: int, total: int):
    """
    Display a flashcard question.

    Args:
        card: Flashcard record
        question_num: Current question number
        total: Total number of questions
    """
    clear_screen()
    print_header(f"QUESTION {question_num} OF {total}")

    print(f"Subject: {card['Subject']} / {card['Subtopic']}")
    print(f"Source: {card['SourceFile']}")
    print("\n" + "-" * 60)
    print(f"Q: {card['Question']}")
    print("-" * 60)


def display_answer(card: Dict):
    """
    Display the answer to a flashcard.

    Args:
        card: Flashcard record
    """
    print("\n" + "=" * 60)
    print("ANSWER:")
    print(f"A: {card['Answer']}")
    print("=" * 60)


def get_user_response() -> str:
    """
    Get user's self-assessment of their answer.

    Returns:
        'y' for correct, 'n' for incorrect, 'q' to quit
    """
    while True:
        try:
            response = input("\nDid you get it right? (y/n, q to quit): ").strip().lower()

            if response in ['y', 'yes']:
                return 'y'
            elif response in ['n', 'no']:
                return 'n'
            elif response in ['q', 'quit', 'exit']:
                return 'q'
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'q' to quit.")

        except KeyboardInterrupt:
            return 'q'


def run_quiz(df: pd.DataFrame, limit: Optional[int] = None) -> Dict:
    """
    Run a complete quiz session.

    Args:
        df: DataFrame of flashcards to quiz
        limit: Maximum number of questions to ask

    Returns:
        Dictionary with quiz results
    """
    if df.empty:
        print("No flashcards to quiz.")
        return {"answered": 0, "correct": 0, "incorrect": 0, "wrong_cards": []}

    # Convert DataFrame to list of dictionaries
    cards = df.to_dict(orient="records")
    random.shuffle(cards)

    # Apply limit if specified
    if limit is not None and limit > 0:
        cards = cards[:limit]

    total_questions = len(cards)
    correct = 0
    incorrect = 0
    wrong_cards = []

    for i, card in enumerate(cards, 1):
        display_question(card, i, total_questions)
        wait_for_enter("Press Enter to see the answer...")
        display_answer(card)

        response = get_user_response()

        if response == 'q':
            print(f"\nQuiz ended early. Answered {i-1} of {total_questions} questions.")
            break
        elif response == 'y':
            correct += 1
            print("✓ Correct!")
        else:  # 'n'
            incorrect += 1
            wrong_cards.append(card)
            print("✗ Incorrect.")

        # Brief pause before next question
        if i < total_questions:
            wait_for_enter("Press Enter for next question...")

    return {
        "answered": correct + incorrect,
        "correct": correct,
        "incorrect": incorrect,
        "wrong_cards": wrong_cards,
        "total_available": total_questions
    }


def display_results(results: Dict):
    """
    Display quiz results and review.

    Args:
        results: Dictionary with quiz results
    """
    clear_screen()
    print_header("QUIZ RESULTS")

    answered = results["answered"]
    correct = results["correct"]
    incorrect = results["incorrect"]
    total_available = results.get("total_available", answered)

    if answered > 0:
        percentage = (correct / answered) * 100
        print(f"Questions answered: {answered} of {total_available}")
        print(f"Correct answers: {correct}")
        print(f"Incorrect answers: {incorrect}")
        print(f"Score: {percentage:.1f}%")

        if percentage >= 90:
            print("🎉 Excellent work!")
        elif percentage >= 80:
            print("👍 Great job!")
        elif percentage >= 70:
            print("📚 Good effort!")
        else:
            print("💪 Keep practicing!")
    else:
        print("No questions were answered.")

    # Review incorrect answers
    if results["wrong_cards"]:
        print(f"\n{'-'*60}")
        print("REVIEW: Questions you got wrong")
        print(f"{'-'*60}")

        for i, card in enumerate(results["wrong_cards"], 1):
            print(f"\n{i}. [{card['Subject']} / {card['Subtopic']}]")
            print(f"Q: {card['Question']}")
            print(f"A: {card['Answer']}")

    print(f"\n{'='*60}")


def select_filters(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Interactive filtering interface for subjects and subtopics.

    Args:
        df: DataFrame of all flashcards

    Returns:
        Filtered DataFrame or None if user cancels
    """
    filtered_df = df.copy()

    while True:
        # Subject selection
        subject_filtered = select_subject(filtered_df)
        if subject_filtered is None:
            return None

        # Subtopic selection
        subtopic_filtered = select_subtopic(subject_filtered)
        if subtopic_filtered is None:
            continue  # Go back to subject selection

        # Question limit selection
        question_limit = select_question_limit()
        if question_limit is None:
            continue  # Go back to subtopic selection

        return subtopic_filtered


def start_quiz_session(df: pd.DataFrame) -> bool:
    """
    Start a complete quiz session with filtering and results.

    Args:
        df: DataFrame of all flashcards

    Returns:
        True if user wants another quiz, False to return to menu
    """
    try:
        # Filter selection
        filtered_df = select_filters(df)
        if filtered_df is None or filtered_df.empty:
            print("No flashcards selected for quiz.")
            wait_for_enter()
            return True

        # Run quiz
        question_limit = select_question_limit()
        results = run_quiz(filtered_df, question_limit)

        # Display results
        display_results(results)

        # Ask if user wants another quiz
        while True:
            try:
                choice = input("\nWould you like to take another quiz? (y/n): ").strip().lower()
                if choice in ['y', 'yes']:
                    return True
                elif choice in ['n', 'no']:
                    return False
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
            except KeyboardInterrupt:
                return False

    except Exception as e:
        print(f"Error during quiz session: {e}")
        wait_for_enter()
        return True


def main_quiz_interface(output_dir):
    """
    Main entry point for the quiz interface.

    Args:
        output_dir: Directory containing Excel flashcard files
    """
    try:
        print("Loading flashcards...")
        df = load_all_records(output_dir)

        if df.empty:
            print("No flashcards found. Please generate some flashcards first.")
            wait_for_enter()
            return

        print(f"Loaded {len(df)} flashcards.")

        # Start quiz loop
        while start_quiz_session(df):
            pass

    except KeyboardInterrupt:
        print("\nReturning to main menu...")
    except Exception as e:
        print(f"Error in quiz interface: {e}")
        wait_for_enter()