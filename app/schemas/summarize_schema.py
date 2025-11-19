from enum import Enum
from pydantic import BaseModel

class SummaryMethod(str, Enum):
    abstractive = "abstractive"
    extractive = "extractive"
    bullet = "bullet"

class SummarizeRequest(BaseModel):
    text: str
    method: SummaryMethod = SummaryMethod.abstractive
