from .base_extractor import BaseExtractor
import easyocr

reader = easyocr.Reader(['en'], gpu=False)


class ImageExtractor(BaseExtractor):

    def extract(self, path: str) -> str:
        try:
            result = reader.readtext(path, detail=0)

            if result:
                return "\n".join(result)

            return "[OCR found no text]"

        except Exception:
            return "[OCR failed]"
