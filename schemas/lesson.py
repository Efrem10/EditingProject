# schemas/lesson.py

from typing import Optional

from pydantic import BaseModel, ConfigDict


# =========================================================
# CREATE LESSON
#
# POST /lesson/section/{section_id}
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

    # -----------------------------------------------------
    # Optional lesson description
    # -----------------------------------------------------

    description: Optional[str] = None


# =========================================================
# UPDATE LESSON
#
# PUT /lesson/lessons/{lesson_id}
#
# All fields are optional so the admin can update only
# the fields that need to be changed.
# =========================================================

class LessonUpdate(BaseModel):

    # -----------------------------------------------------
    # Lesson title
    # -----------------------------------------------------

    title: Optional[str] = None

    # -----------------------------------------------------
    # Lesson description
    # -----------------------------------------------------

    description: Optional[str] = None

    # -----------------------------------------------------
    # Lesson duration
    # Example: "10:30"
    # -----------------------------------------------------

    duration: Optional[str] = None

    # -----------------------------------------------------
    # Free lesson or paid lesson
    # -----------------------------------------------------

    is_free: Optional[bool] = None

    # -----------------------------------------------------
    # Allow moving lesson to another section
    # -----------------------------------------------------

    section_id: Optional[int] = None

    # -----------------------------------------------------
    # Lesson order inside section
    # -----------------------------------------------------

    lesson_number: Optional[int] = None


# =========================================================
# LESSON RESPONSE
#
# Used when returning a lesson from the API.
# =========================================================

class LessonResponse(BaseModel):

    id: int

    title: str

    # -----------------------------------------------------
    # Optional lesson description
    # -----------------------------------------------------

    description: Optional[str] = None

    # -----------------------------------------------------
    # Lesson duration
    # -----------------------------------------------------

    duration: Optional[str] = None

    # -----------------------------------------------------
    # Cloudinary video URL
    # -----------------------------------------------------

    video_url: Optional[str] = None

    # -----------------------------------------------------
    # Free lesson
    # -----------------------------------------------------

    is_free: bool

    # -----------------------------------------------------
    # Course information
    # -----------------------------------------------------

    course_id: int

    # -----------------------------------------------------
    # Section information
    # -----------------------------------------------------

    section_id: int

    # -----------------------------------------------------
    # Lesson order
    # -----------------------------------------------------

    lesson_number: int

    # -----------------------------------------------------
    # Cloudinary public ID
    #
    # Useful for admin operations such as replacing
    # or deleting the video.
    # -----------------------------------------------------

    cloudinary_public_id: Optional[str] = None

    # -----------------------------------------------------
    # Pydantic v2
    # Allows SQLAlchemy model objects to be returned.
    # -----------------------------------------------------

    model_config = ConfigDict(
        from_attributes=True
    )