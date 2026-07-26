from pydantic import BaseModel
from typing import Optional

from schemas.lesson import LessonResponse


class CourseCreate(BaseModel):
    title: str
    description: str
    price: float
    category: str


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: float
    thumbnail: Optional[str]
    category: str
    is_published: bool

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    lessons: list[LessonResponse] = []