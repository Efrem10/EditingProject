from pydantic import BaseModel, Field
from typing import Optional

from schemas.lesson import LessonResponse


# ============================================================
# CREATE SECTION
# ============================================================

class SectionCreate(BaseModel):

    section_number: int

    title: str

    description: Optional[str] = None


# ============================================================
# UPDATE SECTION
#
# All fields are optional so the admin can update only
# the information that needs to be changed.
# ============================================================

class SectionUpdate(BaseModel):

    section_number: Optional[int] = None

    title: Optional[str] = None

    description: Optional[str] = None


# ============================================================
# SECTION RESPONSE
# ============================================================

class SectionResponse(BaseModel):

    id: int

    course_id: int

    section_number: int

    title: str

    description: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# SECTION DETAILS RESPONSE
#
# Includes all lessons belonging to this section.
#
# Course
#   └── Section
#         ├── Lesson 1
#         ├── Lesson 2
#         └── Lesson 3
# ============================================================

class SectionDetailResponse(SectionResponse):

    lessons: list[LessonResponse] = Field(
        default_factory=list
    )

    class Config:
        from_attributes = True