from pydantic import BaseModel
from datetime import datetime


class CertificateResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    certificate_code: str
    issued_at: datetime

    class Config:
        from_attributes = True