from .base_extractor import BaseExtractor


class TextExtractor(BaseExtractor):

    def extract(self, path: str) -> str:
        try:
            # Try UTF-8 first (common for TXT, RTF)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            try:

                with open(path, "rb") as f:
                    raw = f.read()

                encoding = "utf-8"
                return raw.decode(encoding, errors="ignore")

                return raw.decode(encoding, errors="ignore")

            except Exception:
                return "[Failed to read text file]"
