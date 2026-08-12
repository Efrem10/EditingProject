from pydantic import BaseModel
from typing import Optional

from schemas.lesson import LessonResponse


# ==========================
# CREATE COURSE
# ==========================

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str


# ==========================
# COURSE RESPONSE
# ==========================

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: float
    thumbnail: Optional[str] = None
    category: str
    is_published: bool

    class Config:
        from_attributes = True


# ==========================
# COURSE DETAILS RESPONSE
# ==========================

class CourseDetailResponse(CourseResponse):
    lessons: list[LessonResponse] = []

    class Config:
        from_attributes = True