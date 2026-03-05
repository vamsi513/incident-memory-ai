from pydantic import BaseModel, Field


class EvalSample(BaseModel):
    question: str
    expected_parent_ids: list[str] = Field(default_factory=list)


class RetrievalEvalResult(BaseModel):
    question: str
    hit_rate: float
    matched_parent_ids: list[str]


class RetrievalEvalReport(BaseModel):
    total_samples: int
    average_hit_rate: float
    results: list[RetrievalEvalResult]
