# models/section.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
)

from sqlalchemy.orm import relationship

from database import Base


class Section(Base):
    __tablename__ = "sections"

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
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
    # SECTION INFORMATION
    # =====================================================

    section_number = Column(
        Integer,
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    # -----------------------------------------------------
    # Section -> Course
    # -----------------------------------------------------

    course = relationship(
        "Course",
        back_populates="sections"
    )

    # -----------------------------------------------------
    # Section -> Lessons
    # -----------------------------------------------------

    lessons = relationship(
        "Lesson",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Lesson.lesson_number"
    )