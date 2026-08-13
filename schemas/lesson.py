# schemas/lesson.py

from pydantic import BaseModel
from typing import Optional


# =========================================================
# CREATE LESSON
# =========================================================

class LessonCreate(BaseModel):

    title: str

    duration: Optional[str] = None

    is_free: bool = False

    # -----------------------------------------------------
    # Section that this lesson belongs to
    # -----------------------------------------------------

    section_id: int

    # -----------------------------------------------------
    # Lesson order inside the section
    #
    # Example:
    #
    # Section 2: Installations
    #     1. Install XAMPP
    #     2. Install WordPress
    #     3. Configure WordPress
    # -----------------------------------------------------

    lesson_number: int = 1


# =========================================================
# LESSON RESPONSE
# =========================================================

class LessonResponse(BaseModel):

    id: int

    title: str

    duration: Optional[str] = None

    video_url: Optional[str] = None

    is_free: bool

    course_id: int

    # -----------------------------------------------------
    # Section information
    # -----------------------------------------------------

    section_id: int

    lesson_number: int

    class Config:
        from_attributes = True