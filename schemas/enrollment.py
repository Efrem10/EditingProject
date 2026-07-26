from pydantic import BaseModel
from datetime import datetime


class EnrollmentCreate(BaseModel):
    course_id: int


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    status: str
    enrolled_at: datetime

    class Config:
        from_attributes = True