from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from datetime import datetime

from database import Base


class Course(Base):
    __tablename__ = "courses"

    # =====================================================
    # BASIC COURSE INFORMATION
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

    # Short description
    # Appears above the video.
    description = Column(
        Text,
        nullable=True
    )

    # Detailed description
    # Appears below the video.
    detailed_description = Column(
        Text,
        nullable=True
    )

    price = Column(
        Float,
        nullable=False
    )

    category = Column(
        String(100),
        nullable=False
    )

    # =====================================================
    # COURSE COVER IMAGE
    # =====================================================

    thumbnail = Column(
        String(500),
        nullable=True
    )

    thumbnail_public_id = Column(
        String(255),
        nullable=True
    )

    # =====================================================
    # COURSE STATUS
    # =====================================================

    is_published = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # =====================================================
    # CREATOR
    # =====================================================

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    creator = relationship(
        "User",
        back_populates="courses"
    )

    # =====================================================
    # COURSE → SECTIONS → LESSONS
    # =====================================================

    sections = relationship(
        "Section",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Section.section_number"
    )

    # Keep this for compatibility with existing code.
    lessons = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    purchases = relationship(
        "Purchase",
        back_populates="course"
    )

    certificates = relationship(
        "Certificate",
        back_populates="course"
    )