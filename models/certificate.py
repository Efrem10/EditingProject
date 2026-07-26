from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Certificate(Base):
    __tablename__ = "certificates"

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

    certificate_number = Column(
        String(100),
        unique=True,
        nullable=False
    )

    verification_code = Column(
        String(100),
        unique=True,
        nullable=False
    )

    pdf_path = Column(
        String(255),
        nullable=True
    )

    issued_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    is_verified = Column(
        Boolean,
        default=True
    )

    user = relationship(
        "User",
        back_populates="certificates"
    )

    course = relationship(
        "Course",
        back_populates="certificates"
    )