from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PainPostResponse(BaseModel):
    id: int
    source: str
    author: str
    text: str
    url: Optional[str]
    pain_keywords: List[str]
    sentiment_score: float
    pain_intensity: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    keywords: List[str] = ["ненавижу", "проблема", "хочу чтобы"]
    platforms: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
