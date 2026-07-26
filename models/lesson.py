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

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False)

    video_url = Column(String(500), nullable=True)

    duration = Column(String(20), nullable=True)

    is_free = Column(Boolean, default=False)

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    course = relationship(
        "Course",
        back_populates="lessons"
    )
    cloudinary_public_id = Column(
        String(255),
        nullable=True
    )
    progress = relationship(
        "Progress",
        back_populates="lesson"
    )