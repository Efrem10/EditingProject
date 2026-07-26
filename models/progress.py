from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Progress(Base):
    __tablename__ = "progress"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id"),
        nullable=False
    )

    completed = Column(
        Boolean,
        default=False
    )

    completed_at = Column(
        DateTime,
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="progress"
    )

    lesson = relationship(
        "Lesson",
        back_populates="progress"
    )