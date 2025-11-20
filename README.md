# Local AI Flashcard Generator

A comprehensive local flashcard generator and practice tool that uses Llama 2 to convert study notes into Q&A flashcards. Features multi-format text extraction, AI-powered flashcard generation, Excel storage, and an interactive CLI quiz interface.

## Features

- **Multi-format Support**: Extract text from `.txt`, `.md`, `.docx`, and `.pdf` files
- **AI-Powered Generation**: Uses Llama 2 to create high-quality Q&A flashcards
- **Organized Storage**: Saves flashcards to Excel files with metadata (Subject, Subtopic, Source)
- **Interactive Quiz Mode**: CLI-based testing with scoring and review
- **Flexible Configuration**: Configurable chunking, generation parameters, and storage modes
- **Multiple AI Backends**: Support for HuggingFace Transformers, Ollama, and custom HTTP endpoints

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Local Llama 2 model or access to AI backend
- (Optional) CUDA-compatible GPU for faster processing

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Flashcards
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. **Run the application**
   ```bash
   python main.py
   ```

2. **Choose an option**:
   - `1`: Generate flashcards from notes
   - `2`: Take a quiz
   - `3`: View statistics
   - `4`: Configuration info
   - `5`: Exit

## Detailed Usage

### Generating Flashcards

1. **Select root notes folder**: Choose the directory containing your study notes
2. **Select output folder**: Choose where to save the Excel files
3. **Configure parameters**:
   - Cards per chunk (default: 8)
   - AI backend (Transformers, Ollama, or HTTP API)
4. **Wait for processing**: The app will scan, extract, and generate flashcards

### Folder Structure

Organize your notes with the following structure:
```
StudyNotes/
├── Biology/
│   ├── Cell Biology/
│   │   ├── lecture1.pdf
│   │   └── summary.docx
│   └── Genetics/
│       └── mendel_notes.txt
└── Chemistry/
    └── Organic/
        └── reactions.pdf
```

### Quiz Mode

1. **Load flashcards**: Select the folder containing your Excel files
2. **Filter by subject**: Choose specific subjects or all subjects
3. **Filter by subtopic**: Choose specific subtopics or all subtopics
4. **Set question limit**: Choose how many questions to answer
5. **Take the quiz**: Answer questions interactively with self-scoring
6. **Review results**: See your score and review incorrect answers

## Configuration

### AI Backends

#### HuggingFace Transformers (Recommended)
- **Setup**: Requires access to Llama 2 models on Hugging Face
- **Models**: `meta-llama/Llama-2-7b-chat-hf` or similar
- **Performance**: Best with GPU, slower on CPU
- **Offline**: Works completely offline once model is downloaded

#### Ollama
- **Setup**: Install Ollama and pull Llama 2 model
- **Command**: `ollama pull llama2`
- **Performance**: Fast, efficient local serving
- **Convenience**: Easy setup and management

#### HTTP API
- **Setup**: Configure custom endpoint URL
- **Flexibility**: Works with any compatible API
- **Use Case**: For custom or cloud-based LLM services

### Settings (config.py)

- `MAX_CHARS_PER_CHUNK`: Text chunking size (default: 2000)
- `DEFAULT_CARDS_PER_CHUNK`: Flashcards per chunk (default: 8)
- `EXCEL_MODE`: Storage mode ("global" or "per_subject")
- `GLOBAL_EXCEL_FILENAME`: Name for global Excel file

## File Formats

### Input Formats

- **`.txt`**: Plain text files with UTF-8 encoding
- **`.md`**: Markdown files
- **`.docx`**: Microsoft Word documents
- **`.pdf`**: PDF documents (text-based)

### Output Format

Excel files with the following columns:
- **Subject**: Subject category from folder structure
- **Subtopic**: Subtopic category from folder structure
- **SourceFile**: Original filename
- **Question**: Generated question text
- **Answer**: Generated answer text
- **Difficulty**: Reserved for future use
- **CreatedAt**: Timestamp of generation

## Examples

### Command Line Usage

```bash
# Interactive mode
python main.py

# Generate flashcards (requires interactive setup)
# Select option 1, then follow prompts

# Take quiz (requires existing flashcards)
# Select option 2, then follow prompts
```

### Python API Usage

```python
from text_extraction import iter_note_files
from flashcard_generator import generate_flashcards_for_files
from excel_store import save_records
from ai_client import create_ai_client

# Initialize AI client
ai_client = create_ai_client("transformers", model_name="meta-llama/Llama-2-7b-chat-hf")

# Scan files
files_info = list(iter_note_files(Path("StudyNotes")))

# Generate flashcards
results = generate_flashcards_for_files(ai_client, files_info)

# Save to Excel
for subject, records in results.items():
    save_records(Path("output"), subject, records)
```

## Troubleshooting

### Common Issues

1. **Model Loading Errors**
   - Ensure you have access to Llama 2 models on Hugging Face
   - Check if transformers and torch are properly installed
   - Verify GPU drivers if using CUDA

2. **Memory Issues**
   - Reduce `MAX_CHARS_PER_CHUNK` in config.py
   - Use smaller models or quantized versions
   - Ensure sufficient RAM/VRAM

3. **File Processing Errors**
   - Check file permissions and accessibility
   - Verify supported file formats
   - Look for corrupted or password-protected files

4. **Excel Export Issues**
   - Ensure output directory is writable
   - Check if Excel files are not open in other programs
   - Verify pandas and openpyxl installation

### Performance Optimization

- **GPU Acceleration**: Use CUDA-enabled PyTorch for faster processing
- **Chunking**: Adjust chunk size based on your model's context window
- **Batch Processing**: Process multiple files in sequence for efficiency
- **Model Selection**: Choose appropriate model size for your hardware

## Development

### Project Structure

```
Flashcards/
├── config.py              # Configuration management
├── ai_client.py            # AI model abstraction layer
├── text_extraction.py      # File scanning and text extraction
├── flashcard_generator.py  # Main processing pipeline
├── excel_store.py          # Excel file operations
├── quiz_cli.py            # Interactive quiz interface
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Testing

```bash
# Test individual components
python -m pytest tests/

# Test the full application
python main.py
```

## Requirements

See `requirements.txt` for full dependency list:

- **pandas**: Data manipulation and Excel operations
- **openpyxl**: Excel file format support
- **python-docx**: Word document processing
- **pdfplumber**: PDF text extraction
- **transformers**: HuggingFace model integration
- **torch**: PyTorch for model operations

## License

[Add your license information here]

## Support

For issues and questions:
1. Check this README for common solutions
2. Review the troubleshooting section
3. Check existing issues in the repository
4. Create a new issue with detailed information

## Roadmap

### Version 1.0
- ✅ Core flashcard generation
- ✅ Multi-format text extraction
- ✅ Excel storage
- ✅ CLI quiz interface
- ✅ Multiple AI backends

### Future Versions
- [ ] GUI interface (Tkinter/PyQt)
- [ ] Additional file formats (.pptx, image OCR)
- [ ] Advanced AI features (difficulty auto-detection)
- [ ] Performance optimizations (parallel processing)
- [ ] Backup and sync capabilities
- [ ] Statistical analysis of quiz performance
- [ ] Import/export functionality
- [ ] Mobile app companion