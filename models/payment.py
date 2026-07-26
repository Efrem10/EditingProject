from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Payment(Base):
    __tablename__ = "payments"

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

    amount = Column(Float, nullable=False)

    transaction_id = Column(
        String(255),
        unique=True,
        nullable=True
    )

    gateway = Column(
        String(50),
        default="simulation",
        nullable=False
    )

    payment_method = Column(
        String(50),
        nullable=True
    )

    status = Column(
        String(20),
        default="pending"
    )

    verified = Column(
        Boolean,
        default=False
    )

    paid_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship("User")

    course = relationship("Course")