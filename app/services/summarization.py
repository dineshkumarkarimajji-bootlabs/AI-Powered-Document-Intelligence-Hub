import requests
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO)


class SummarizerService:
    """
    Summarization logic using Ollama (Llama-3).
    Uses base_url to send requests to Ollama API.
    """

    def __init__(self, model_name: str = None):
        # Model name (default: llama3)
        self.model_name =  settings.OLLAMA_MODEL


    def _call_ollama(self, prompt: str) -> str:
        """
        Send prompt to LLM using Ollama's /api/generate endpoint.
        """

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(
                url="http://localhost:11434/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result_text = response.json().get("response", "")
            return result_text.strip()

        except Exception as e:
            logging.error(f"Ollama request failed: {e}")
            raise RuntimeError(f"Ollama error: {e}")

    def summarize(self, text: str, method: str = "abstractive") -> str:
        """
        Summarize text in different modes:
        - abstractive
        - extractive
        - bullet
        """

        if method == "extractive":
            prompt = f"""
            Extract the most important FACTUAL sentences from the following text.
            Do NOT rewrite, only extract key sentences.

            TEXT:
            {text}
            """

        elif method == "bullet":
            prompt = f"""
            Summarize the following text into clean bullet points.
            Keep bullets short and meaningful.

            TEXT:
            {text}
            """

        else:  # abstractive summary
            prompt = f"""
            Provide a clear and short summary for the following text:

            TEXT:
            {text}
            """

        return self._call_ollama(prompt)


# Global instance
summarizer = SummarizerService()
