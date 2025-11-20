"""
web_app.py

Flask web application for the AI Flashcard Generator.
Provides a browser-based interface for generating flashcards from uploaded files using local Llama.
"""

import os
import json
import zipfile
import tempfile
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

# Create Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'txt', 'md', 'docx', 'pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def call_llama(prompt, max_tokens=500):
    """
    Call local Llama installation using command line.

    Args:
        prompt: The prompt to send to Llama
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text as string
    """
    try:
        # Try different ways to call Llama
        llama_commands = [
            ['ollama', 'run', 'llama2', prompt],
            ['llama', '--prompt', prompt, '--max-tokens', str(max_tokens)],
            ['python', '-c', f'import llama; print(llama.generate("{prompt}", max_tokens={max_tokens}))']
        ]

        for cmd in llama_commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=60,
                    check=True
                )
                if result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        # If none of the commands worked, try a simple HTTP request to common Llama servers
        try:
            import requests
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama2',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('response', '')
        except:
            pass

        return "Error: Could not connect to Llama. Please ensure Llama is installed and running."

    except Exception as e:
        return f"Error calling Llama: {str(e)}"


def extract_text_from_file(file_path):
    """Extract text from uploaded file."""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    try:
        if extension in {'.txt', '.md'}:
            return file_path.read_text(encoding='utf-8')
        elif extension == '.docx':
            try:
                import docx
                doc = docx.Document(str(file_path))
                return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
            except ImportError:
                return "Error: python-docx not installed. Install with: pip install python-docx"
        elif extension == '.pdf':
            try:
                import pdfplumber
                text = []
                with pdfplumber.open(str(file_path)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text)
                return '\n'.join(text)
            except ImportError:
                return "Error: pdfplumber not installed. Install with: pip install pdfplumber"
        else:
            return f"Error: Unsupported file type {extension}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def generate_flashcards_from_text(text, subject="General", subtopic="General", source_file="unknown"):
    """
    Generate flashcards from text using Llama.

    Args:
        text: Input text
        subject: Subject category
        subtopic: Subtopic category
        source_file: Source filename

    Returns:
        List of flashcard dictionaries
    """
    # Split text into chunks for processing
    chunks = []
    max_chunk_size = 2000
    words = text.split()
    current_chunk = []
    current_size = 0

    for word in words:
        if current_size + len(word) + 1 > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    all_flashcards = []

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue

        prompt = f"""
You are a helpful study assistant. Create 5 high-quality flashcards from the text below.
Each flashcard should test important concepts, definitions, or relationships.

Requirements:
- Return ONLY a JSON array of objects
- Each object must have "question" and "answer" fields
- Questions should be clear and specific
- Answers should be accurate and concise
- No extra commentary outside the JSON

Text: {chunk}

JSON flashcards:
"""

        try:
            response = call_llama(prompt)

            # Try to parse JSON from response
            start = response.find('[')
            end = response.rfind(']') + 1

            if start != -1 and end > start:
                json_str = response[start:end]
                flashcards = json.loads(json_str)

                if isinstance(flashcards, list):
                    for card in flashcards:
                        if isinstance(card, dict) and 'question' in card and 'answer' in card:
                            all_flashcards.append({
                                'subject': subject,
                                'subtopic': subtopic,
                                'source_file': source_file,
                                'question': card['question'].strip(),
                                'answer': card['answer'].strip(),
                                'difficulty': '',
                                'created_at': datetime.now().isoformat()
                            })

        except Exception as e:
            print(f"Error processing chunk {i}: {e}")
            continue

    return all_flashcards


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process files."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    subject = request.form.get('subject', 'General')
    subtopic = request.form.get('subtopic', 'General')

    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400

    all_flashcards = []
    processed_files = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Extract text from file
            text = extract_text_from_file(filepath)

            if text.startswith('Error:'):
                processed_files.append({
                    'filename': filename,
                    'status': 'error',
                    'message': text
                })
                continue

            # Generate flashcards
            flashcards = generate_flashcards_from_text(text, subject, subtopic, filename)

            if flashcards:
                all_flashcards.extend(flashcards)
                processed_files.append({
                    'filename': filename,
                    'status': 'success',
                    'cards_generated': len(flashcards)
                })
            else:
                processed_files.append({
                    'filename': filename,
                    'status': 'warning',
                    'message': 'No flashcards generated'
                })

            # Clean up uploaded file
            os.remove(filepath)
        else:
            processed_files.append({
                'filename': file.filename,
                'status': 'error',
                'message': 'Invalid file type'
            })

    # Save flashcards to Excel
    if all_flashcards:
        excel_filename = f"{subject.replace(' ', '_')}_flashcards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        excel_path = os.path.join(app.config['OUTPUT_FOLDER'], excel_filename)

        try:
            import pandas as pd
            df = pd.DataFrame(all_flashcards)
            df.to_excel(excel_path, index=False)
            download_url = url_for('download_file', filename=excel_filename)
        except ImportError:
            download_url = None
            excel_filename = None
    else:
        download_url = None
        excel_filename = None

    return jsonify({
        'success': True,
        'flashcards': all_flashcards,
        'processed_files': processed_files,
        'total_cards': len(all_flashcards),
        'download_url': download_url,
        'excel_filename': excel_filename
    })


@app.route('/download/<filename>')
def download_file(filename):
    """Download generated Excel file."""
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True
    )


@app.route('/quiz')
def quiz():
    """Render quiz page with flashcards."""
    return render_template('quiz.html')


@app.route('/api/flashcards')
def get_flashcards():
    """API endpoint to get flashcards for quiz."""
    # For now, return a sample set
    sample_flashcards = [
        {
            'question': 'What is the powerhouse of the cell?',
            'answer': 'The mitochondria'
        },
        {
            'question': 'What is the basic unit of life?',
            'answer': 'The cell'
        },
        {
            'question': 'What does ATP stand for?',
            'answer': 'Adenosine Triphosphate'
        }
    ]
    return jsonify(sample_flashcards)


@app.route('/api/test-llama')
def test_llama():
    """Test connection to Llama."""
    try:
        response = call_llama("Hello, how are you?", max_tokens=50)
        if response and not response.startswith('Error:'):
            return jsonify({'success': True, 'response': response})
        else:
            return jsonify({'success': False, 'error': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/about')
def about():
    """Render about page."""
    return render_template('about.html')


if __name__ == '__main__':
    print("🚀 Starting AI Flashcard Generator Web App...")
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("📝 Upload your study notes to generate flashcards!")

    # Test Llama connection on startup
    try:
        print("🤖 Testing Llama connection...")
        test_response = call_llama("Hello", max_tokens=10)
        if not test_response.startswith('Error:'):
            print("✅ Llama connection successful!")
        else:
            print("❌ Llama connection failed. Please ensure Llama is installed and running.")
            print("   Install options:")
            print("   - Ollama: https://ollama.ai/")
            print("   - Local Llama: https://github.com/facebookresearch/llama")
    except Exception as e:
        print(f"❌ Error testing Llama: {e}")

    app.run(debug=True, host='0.0.0.0', port=5000)