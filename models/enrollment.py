from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    String
)
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    status = Column(
        String(20),
        default="active"
    )

    enrolled_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship(
        "User",
        back_populates="enrollments"
    )

    course = relationship(
        "Course",
        back_populates="enrollments"
    )