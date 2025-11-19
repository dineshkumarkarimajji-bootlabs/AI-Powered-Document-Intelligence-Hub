from enum import Enum
from pydantic import BaseModel

class FormatMethod(str, Enum):
    markdown = "markdown"
    json = "json"
    table = "table"

class FormatRequest(BaseModel):
    text: str
    format: FormatMethod

class FormatResponse(BaseModel):
    formatted_text: str