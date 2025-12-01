from app.services.transcription_service import transcription_service
from .base_extractor import BaseExtractor
import os


class AudioExtractor(BaseExtractor):

    def extract(self, path: str) -> str:
        try:
            # Validate audio format
            ext = os.path.splitext(path)[1].lower()
            if ext not in [".mp3", ".wav", ".m4a", ".aac", ".mp4"]:
                return f"[Unsupported audio format: {ext}]"

            # Perform transcription
            text = transcription_service.transcribe(path)

            if not text or not str(text).strip():
                return "[Transcription returned empty text]"

            return text

        except FileNotFoundError:
            return "[Audio file not found]"

        except PermissionError:
            return "[Permission denied reading audio file]"

        except Exception as e:
            
            return f"[Failed to transcribe audio: {str(e)}]"
