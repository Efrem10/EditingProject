from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base


class LiveClass(Base):

    __tablename__ = "live_classes"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    description = Column(String, nullable=True)

    duration = Column(String, nullable=True)

    course_id = Column(Integer, ForeignKey("courses.id"))

    meeting_provider = Column(String, nullable=False)

    meeting_link = Column(String, nullable=True)

    scheduled_at = Column(DateTime)

    status = Column(String, default="scheduled")
