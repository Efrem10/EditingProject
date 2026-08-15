from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from schemas.lesson import LessonResponse


# ============================================================
# CREATE SECTION
#
# POST /section/course/{course_id}
#
# Used when creating a new section.
# ============================================================

class SectionCreate(BaseModel):

    section_number: int = Field(
        ...,
        ge=1,
        description="Section number inside the course."
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Section title."
    )

    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional section description."
    )


# ============================================================
# UPDATE SECTION
#
# PUT /section/{section_id}
#
# All fields are optional.
#
# This allows the admin to update:
#
# - section number only
# - title only
# - description only
# - or all fields
# ============================================================

class SectionUpdate(BaseModel):

    section_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="New section number."
    )

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New section title."
    )

    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="New section description."
    )


# ============================================================
# LESSON INSIDE SECTION
#
# This response is useful when loading:
#
# Course
#   └── Section
#        ├── Lesson 1
#        ├── Lesson 2
#        └── Lesson 3
#
# LessonResponse already contains the lesson information.
# ============================================================


# ============================================================
# SECTION RESPONSE
#
# Used for:
#
# GET /section/course/{course_id}
# GET /section/{section_id}
# POST /section/course/{course_id}
# PUT /section/{section_id}
# ============================================================

class SectionResponse(BaseModel):

    id: int

    course_id: int

    section_number: int

    title: str

    description: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# SECTION DETAIL RESPONSE
#
# Includes all lessons belonging to this section.
#
# Example:
#
# {
#     "id": 1,
#     "course_id": 10,
#     "section_number": 1,
#     "title": "Introduction",
#     "description": "Introduction to the course",
#     "lessons": [
#         {
#             "id": 1,
#             "title": "Welcome",
#             "lesson_number": 1
#         },
#         {
#             "id": 2,
#             "title": "Getting Started",
#             "lesson_number": 2
#         }
#     ]
# }
# ============================================================

class SectionDetailResponse(SectionResponse):

    lessons: list[LessonResponse] = Field(
        default_factory=list
    )

    model_config = ConfigDict(
        from_attributes=True
    )