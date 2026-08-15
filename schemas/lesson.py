# schemas/lesson.py

from pydantic import BaseModel, ConfigDict
from typing import Optional


# =========================================================
# CREATE LESSON
# =========================================================

class LessonCreate(BaseModel):

    title: str

    duration: Optional[str] = None

    is_free: bool = False

    # -----------------------------------------------------
    # Section this lesson belongs to
    # -----------------------------------------------------

    section_id: int

    # -----------------------------------------------------
    # Lesson order inside the section
    # -----------------------------------------------------

    lesson_number: int = 1


# =========================================================
# UPDATE LESSON
#
# Used when editing an existing lesson.
#
# PUT /lesson/lessons/{lesson_id}
# =========================================================

class LessonUpdate(BaseModel):

    title: Optional[str] = None

    duration: Optional[str] = None

    is_free: Optional[bool] = None

    # -----------------------------------------------------
    # Allow moving lesson to another section
    # -----------------------------------------------------

    section_id: Optional[int] = None

    # -----------------------------------------------------
    # Allow changing lesson order
    # -----------------------------------------------------

    lesson_number: Optional[int] = None


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

    # -----------------------------------------------------
    # Optional description
    #
    # Your backend already uses getattr(lesson, "description",
    # None), so this allows the response to include it if
    # your Lesson model has a description column.
    # -----------------------------------------------------

    description: Optional[str] = None

    # -----------------------------------------------------
    # Cloudinary information
    #
    # Useful for admin editing.
    # -----------------------------------------------------

    cloudinary_public_id: Optional[str] = None

    # -----------------------------------------------------
    # Pydantic v2
    # -----------------------------------------------------

    model_config = ConfigDict(
        from_attributes=True
    )