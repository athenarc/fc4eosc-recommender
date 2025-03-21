from datetime import date
from typing import Optional

from pydantic import BaseModel


class Recommendation(BaseModel):
    result_id: str
    result_title: str
    result_authors: str
    result_type: str
    result_publication_date: Optional[date]
    result_publisher: Optional[str]
    similarity_score: float
