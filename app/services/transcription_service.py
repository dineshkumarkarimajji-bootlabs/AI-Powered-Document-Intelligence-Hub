import os
import whisper


class TranscriptionService:
    def __init__(self, model_name: str = "small"):
        try:
            self.model = whisper.load_model(model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {e}")

    def transcribe(self, file_path: str) -> str:
        """Convert audio → text locally using Whisper (offline)."""

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        try:
            result = self.model.transcribe(
                file_path,
                fp16=False,        # Needed on CPU + MPS
                language="en",     # Helps accuracy
                verbose=False
            )
            return result.get("text", "")
        except Exception as e:
            return f"[Transcription Failed] {str(e)}"


transcription_service = TranscriptionService()
