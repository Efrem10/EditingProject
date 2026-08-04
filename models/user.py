from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    email = Column(String(100), unique=True, index=True, nullable=False)

    # NULL for Google Sign-In users
    password = Column(String(255), nullable=True)

    role = Column(String(20), default="student", nullable=False)

    # Google authentication
    google_id = Column(String(255), unique=True, nullable=True)

    profile_picture = Column(String(500), nullable=True)

    courses = relationship(
        "Course",
        back_populates="creator"
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    progress = relationship(
        "Progress",
        back_populates="user"
    )

    purchases = relationship(
        "Purchase",
        back_populates="user"
    )

    certificates = relationship(
        "Certificate",
        back_populates="user"
    )