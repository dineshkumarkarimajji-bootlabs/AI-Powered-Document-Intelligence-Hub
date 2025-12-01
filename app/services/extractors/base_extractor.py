from abc import ABC, abstractmethod

class BaseExtractor(ABC):


    @abstractmethod
    def extract(self, path: str) -> str:
        raise NotImplementedError("Extractor must implement extract()")

