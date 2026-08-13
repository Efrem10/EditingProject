# models/lesson.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
)

from sqlalchemy.orm import relationship

from database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    # =====================================================
    # BASIC LESSON INFORMATION
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    # =====================================================
    # VIDEO
    # =====================================================

    video_url = Column(
        String(500),
        nullable=True
    )

    duration = Column(
        String(20),
        nullable=True
    )

    # =====================================================
    # LESSON ACCESS
    # =====================================================

    is_free = Column(
        Boolean,
        default=False
    )

    # =====================================================
    # LESSON NUMBER
    #
    # Example:
    #
    # Section 2: Installations
    #     Lesson 1
    #     Lesson 2
    #     Lesson 3
    #
    # lesson_number stores 1, 2, 3...
    # =====================================================

    lesson_number = Column(
        Integer,
        nullable=False,
        default=1
    )

    # =====================================================
    # COURSE
    # =====================================================

    course_id = Column(
        Integer,
        ForeignKey(
            "courses.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================================
    # SECTION
    #
    # Every lesson belongs to one section.
    # =====================================================

    section_id = Column(
        Integer,
        ForeignKey(
            "sections.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    # -----------------------------------------------------
    # Lesson -> Course
    # -----------------------------------------------------

    course = relationship(
        "Course",
        back_populates="lessons"
    )

    # -----------------------------------------------------
    # Lesson -> Section
    # -----------------------------------------------------

    section = relationship(
        "Section",
        back_populates="lessons"
    )

    # =====================================================
    # CLOUDINARY
    # =====================================================

    cloudinary_public_id = Column(
        String(255),
        nullable=True
    )

    # =====================================================
    # PROGRESS
    # =====================================================

    progress = relationship(
        "Progress",
        back_populates="lesson"
    )