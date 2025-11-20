"""
ai_client.py

Abstraction layer for calling Llama 2 (or any other local LLM).
Supports multiple backends: HuggingFace transformers, Ollama, HTTP endpoints.
Designed for easy swapping of different Llama 2 implementations.
"""

from typing import List, Dict, Optional
import json
import time
import requests
from abc import ABC, abstractmethod

# HuggingFace transformers (can be swapped for other implementations)
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from config import DEFAULT_MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_MAX_NEW_TOKENS


class AIModelInterface(ABC):
    """Abstract base class for AI model implementations."""

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass


class TransformersAIModel(AIModelInterface):
    """HuggingFace transformers implementation of Llama 2."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: str = "cpu"):
        """
        Initialize the transformers pipeline.

        Args:
            model_name: Name of the model to use
            device: Device to run on ("cpu" or "cuda")
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers library not available. Install with: pip install transformers torch")

        self.model_name = model_name
        self.device = device

        try:
            print(f"[INFO] Loading model {model_name}...")
            self.pipe = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=model_name,
                device=0 if device == "cuda" else -1,
                max_new_tokens=DEFAULT_MAX_NEW_TOKENS,
                torch_dtype="auto",
            )
            print("[INFO] Model loaded successfully")
        except Exception as e:
            raise Exception(f"Failed to load model {model_name}: {e}")

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the transformers pipeline.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        try:
            outputs = self.pipe(
                prompt,
                do_sample=True,
                temperature=kwargs.get("temperature", DEFAULT_TEMPERATURE),
                num_return_sequences=1,
                pad_token_id=self.pipe.tokenizer.eos_token_id,
            )
            return outputs[0]["generated_text"]
        except Exception as e:
            raise Exception(f"Failed to generate text: {e}")


class OllamaAIModel(AIModelInterface):
    """Ollama HTTP API implementation."""

    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.

        Args:
            model_name: Name of the Ollama model
            base_url: Base URL for Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{base_url}/api/generate"

        # Test connection
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise Exception("Ollama API not responding")
        except requests.RequestException as e:
            raise Exception(f"Cannot connect to Ollama at {base_url}: {e}")

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama API.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", DEFAULT_TEMPERATURE),
                    "num_predict": kwargs.get("max_tokens", DEFAULT_MAX_NEW_TOKENS),
                }
            }

            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")
        except requests.RequestException as e:
            raise Exception(f"Failed to generate text with Ollama: {e}")


class HTTPAIModel(AIModelInterface):
    """Generic HTTP API implementation for custom LLM endpoints."""

    def __init__(self, api_url: str, headers: Optional[Dict] = None, payload_template: Optional[Dict] = None):
        """
        Initialize HTTP client.

        Args:
            api_url: API endpoint URL
            headers: HTTP headers for requests
            payload_template: Template for request payload
        """
        self.api_url = api_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.payload_template = payload_template or {}

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using HTTP API.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        try:
            payload = self.payload_template.copy()
            payload["prompt"] = prompt
            payload.update(kwargs)

            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=60)
            response.raise_for_status()

            result = response.json()
            # Try common response field names
            for field in ["response", "text", "generated_text", "output"]:
                if field in result:
                    return result[field]

            # If no standard field found, return the whole response
            return json.dumps(result)
        except requests.RequestException as e:
            raise Exception(f"Failed to generate text with HTTP API: {e}")


class FlashcardAIClient:
    """Main client for generating flashcards using various AI backends."""

    def __init__(self, backend: str = "transformers", **backend_kwargs):
        """
        Initialize the AI client with specified backend.

        Args:
            backend: Backend type ("transformers", "ollama", "http")
            **backend_kwargs: Backend-specific configuration
        """
        self.backend = backend

        if backend == "transformers":
            self.model = TransformersAIModel(**backend_kwargs)
        elif backend == "ollama":
            self.model = OllamaAIModel(**backend_kwargs)
        elif backend == "http":
            self.model = HTTPAIModel(**backend_kwargs)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def _build_prompt(self, text: str, num_cards: int) -> str:
        """
        Build a structured prompt for flashcard generation.

        Args:
            text: Input text to create flashcards from
            num_cards: Number of flashcards to generate

        Returns:
            Formatted prompt string
        """
        return (
            "You are a helpful study assistant and an expert at creating educational flashcards.\n"
            f"Create up to {num_cards} high-quality flashcards from the text below.\n"
            "Each flashcard should test understanding of important concepts, definitions, or relationships.\n"
            "Make questions clear and specific; make answers concise but complete.\n\n"
            "Requirements:\n"
            "- Return ONLY a JSON array of objects\n"
            "- Each object must have exactly two fields: 'question' and 'answer'\n"
            "- Questions should be clear and test important concepts\n"
            "- Answers should be accurate and concise\n"
            "- No additional text, explanations, or commentary outside the JSON\n"
            "- Valid JSON format only: [{\"question\": \"...\", \"answer\": \"...\"}, ...]\n\n"
            f"Text to process:\n{text}\n\n"
            "JSON flashcards:"
        )

    def _parse_json_response(self, response_text: str) -> List[Dict[str, str]]:
        """
        Parse JSON array from model response with robust error handling.

        Args:
            response_text: Raw text response from model

        Returns:
            List of flashcard dictionaries

        Raises:
            ValueError: If JSON parsing fails or format is invalid
        """
        try:
            # Try to extract JSON array from response
            # Look for the first '[' and the last ']'
            start = response_text.find("[")
            end = response_text.rfind("]")

            if start == -1 or end == -1 or end <= start:
                raise ValueError("No JSON array found in response")

            json_str = response_text[start : end + 1]
            data = json.loads(json_str)

            if not isinstance(data, list):
                raise ValueError("Response is not a JSON array")

            # Validate and clean flashcard data
            flashcards = []
            for item in data:
                if isinstance(item, dict):
                    question = str(item.get("question", "")).strip()
                    answer = str(item.get("answer", "")).strip()

                    if question and answer:
                        flashcards.append({
                            "question": question,
                            "answer": answer
                        })

            return flashcards

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error processing response: {e}")

    def generate_flashcards_from_text(self, text: str, num_cards: int = 8, max_retries: int = 3) -> List[Dict[str, str]]:
        """
        Generate flashcards from text using the AI model.

        Args:
            text: Input text to create flashcards from
            num_cards: Number of flashcards to generate
            max_retries: Maximum number of retry attempts

        Returns:
            List of flashcard dictionaries with 'question' and 'answer' keys

        Raises:
            ValueError: If generation fails after all retries
        """
        if not text or not text.strip():
            return []

        prompt = self._build_prompt(text.strip(), num_cards)

        for attempt in range(max_retries):
            try:
                response_text = self.model.generate_text(prompt)
                flashcards = self._parse_json_response(response_text)

                if flashcards:
                    return flashcards
                else:
                    print(f"[WARN] No valid flashcards generated in attempt {attempt + 1}")

            except Exception as e:
                print(f"[WARN] Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Brief delay between retries
                else:
                    raise ValueError(f"Failed to generate flashcards after {max_retries} attempts: {e}")

        return []


def create_ai_client(backend_type: str = "transformers", **kwargs) -> FlashcardAIClient:
    """
    Factory function to create an AI client.

    Args:
        backend_type: Type of backend to use
        **kwargs: Backend-specific configuration

    Returns:
        Configured FlashcardAIClient instance
    """
    return FlashcardAIClient(backend=backend_type, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Example of creating and testing the AI client
    try:
        # Try with transformers backend
        client = create_ai_client("transformers", model_name=DEFAULT_MODEL_NAME)

        test_text = """
        The mitochondria is the powerhouse of the cell. It converts glucose into ATP through cellular respiration.
        This process occurs in three main stages: glycolysis, the Krebs cycle, and the electron transport chain.
        """

        flashcards = client.generate_flashcards_from_text(test_text, num_cards=3)
        print("Generated flashcards:")
        for i, card in enumerate(flashcards, 1):
            print(f"{i}. Q: {card['question']}")
            print(f"   A: {card['answer']}")

    except Exception as e:
        print(f"Error testing AI client: {e}")
        print("Note: This requires a properly configured Llama 2 model")