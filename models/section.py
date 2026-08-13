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

    # ============================================================
    # BASIC INFORMATION
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ============================================================
    # COURSE
    # ============================================================

    course_id = Column(
        Integer,
        ForeignKey(
            "courses.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # ============================================================
    # SECTION INFORMATION
    # ============================================================

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

    # ============================================================
    # SECTION -> COURSE
    # ============================================================

    course = relationship(
        "Course",
        back_populates="sections"
    )

    # ============================================================
    # SECTION -> LESSONS
    #
    # Lessons are now stored inside sections.
    #
    # We do NOT use lesson_number because your current
    # lessons table does not have that column.
    # ============================================================

    lessons = relationship(
        "Lesson",
        back_populates="section",
        cascade="all, delete-orphan"
    )