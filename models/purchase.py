from sqlalchemy import (
    Column,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Purchase(Base):
    __tablename__ = "purchases"

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

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    payment_status = Column(
        Boolean,
        default=False
    )

    purchased_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    user = relationship(
        "User",
        back_populates="purchases"
    )


    course = relationship(
        "Course",
        back_populates="purchases"
    )