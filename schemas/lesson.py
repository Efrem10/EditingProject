from pydantic import BaseModel
from typing import Optional


class LessonCreate(BaseModel):
    title: str
    duration: Optional[str] = None
    is_free: bool = False


class LessonResponse(BaseModel):
    id: int
    title: str
    duration: Optional[str]
    video_url: Optional[str]
    is_free: bool
    course_id: int

    class Config:
        from_attributes = True