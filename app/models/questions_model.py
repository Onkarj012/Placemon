from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class SampleTestCase(BaseModel):
    input: str
    output: str

class HiddenTestCase(BaseModel):
    input: str
    output: str

class CodingQuestion(BaseModel):
    id: str
    title: str
    description: str
    topics: List[str]
    estimated_time_min: int
    input_format: str
    output_format: str
    constraints: str
    sample_testcases: List[SampleTestCase]
    hidden_testcases: List[HiddenTestCase]
    hints: List[str]
    canonical_solution: Optional[str]

class AptitudeQuestion(BaseModel):
    id: str
    question_type: str   # "mcq" or "short_answer"
    topic: str
    difficulty: str
    question_text: str
    options: Optional[List[str]] = None
    correct_option_index: Optional[int] = None
    short_answer: Optional[str] = None
    step_by_step_solution: List[str]
    final_answer_explanation: str
    hints: List[str]
    estimated_time_sec: int
