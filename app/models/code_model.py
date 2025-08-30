
from pydantic import BaseModel

class CodeSubmission(BaseModel):
    source_code: str
    language_id: int
    stdin: str = ""