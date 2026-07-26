from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)

    site_name = Column(String, default="EditingPro")

    support_email = Column(String, default="")

    phone = Column(String, default="")

    address = Column(String, default="")

    logo = Column(String, nullable=True)

    theme = Column(String, default="light")

    primary_color = Column(String, default="blue")

    language = Column(String, default="English")

    timezone = Column(String, default="Africa/Addis_Ababa")

    allow_registration = Column(Boolean, default=True)

    maintenance_mode = Column(Boolean, default=False)

    live_provider = Column(String, default="Jitsi")