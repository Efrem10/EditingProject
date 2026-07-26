from pydantic import BaseModel
from datetime import datetime


class ProgressResponse(BaseModel):
    id: int
    user_id: int
    lesson_id: int
    completed: bool
    completed_at: datetime

    class Config:
        from_attributes = True