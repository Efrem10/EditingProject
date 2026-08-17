from typing import Optional

from pydantic import BaseModel, ConfigDict


# ============================================================
# CREATE LESSON
#
# POST /lesson/section/{section_id}
#
# section_id comes from the URL.
# lesson_number is generated automatically by the backend.
#
# React sends:
#
# {
#     "title": "Introduction to Django",
#     "duration": "07:30",
#     "is_free": false
# }
# ============================================================

class LessonCreate(BaseModel):

    title: str

    duration: Optional[str] = None

    is_free: bool = False


# ============================================================
# UPDATE LESSON
#
# PUT /lesson/lessons/{lesson_id}
# ============================================================

class LessonUpdate(BaseModel):

    title: Optional[str] = None

    duration: Optional[str] = None

    is_free: Optional[bool] = None

    section_id: Optional[int] = None

    lesson_number: Optional[int] = None


# ============================================================
# LESSON RESPONSE
# ============================================================

class LessonResponse(BaseModel):

    id: int

    title: str

    duration: Optional[str] = None

    video_url: Optional[str] = None

    is_free: bool

    course_id: int

    section_id: int

    lesson_number: int

    cloudinary_public_id: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )