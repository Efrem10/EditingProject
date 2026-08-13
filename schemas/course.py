from pydantic import BaseModel, Field
from typing import Optional

from schemas.lesson import LessonResponse


# =========================================================
# SECTION RESPONSE
# =========================================================

class SectionResponse(BaseModel):

    id: int

    course_id: int

    section_number: int

    title: str

    description: Optional[str] = None

    # -----------------------------------------------------
    # Lessons inside this section
    # -----------------------------------------------------

    lessons: list[LessonResponse] = Field(
        default_factory=list
    )

    class Config:
        from_attributes = True


# =========================================================
# CREATE COURSE
# =========================================================

class CourseCreate(BaseModel):

    title: str

    # -----------------------------------------------------
    # Short description
    # Appears above the video.
    # -----------------------------------------------------

    description: Optional[str] = None

    # -----------------------------------------------------
    # Detailed description
    # Appears below the video.
    # -----------------------------------------------------

    detailed_description: Optional[str] = None

    price: float

    category: str


# =========================================================
# COURSE RESPONSE
# =========================================================

class CourseResponse(BaseModel):

    id: int

    title: str

    # -----------------------------------------------------
    # Short course description
    # -----------------------------------------------------

    description: Optional[str] = None

    # -----------------------------------------------------
    # Detailed course description
    # -----------------------------------------------------

    detailed_description: Optional[str] = None

    price: float

    thumbnail: Optional[str] = None

    category: str

    is_published: bool

    class Config:
        from_attributes = True


# =========================================================
# COURSE DETAILS RESPONSE
# =========================================================

class CourseDetailResponse(CourseResponse):

    # -----------------------------------------------------
    # Course
    #    ↓
    # Sections
    #    ↓
    # Lessons
    # -----------------------------------------------------

    sections: list[SectionResponse] = Field(
        default_factory=list
    )

    # -----------------------------------------------------
    # Keep lessons temporarily for compatibility
    # with existing frontend/backend code.
    # -----------------------------------------------------

    lessons: list[LessonResponse] = Field(
        default_factory=list
    )

    class Config:
        from_attributes = True