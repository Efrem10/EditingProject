from pydantic import BaseModel
from datetime import datetime

from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class LiveClassCreate(BaseModel):
    title: str
    course_id: int
    meeting_provider: str
    scheduled_at: datetime
    duration: Optional[str] = None
    description: Optional[str] = None
    meeting_link: Optional[str] = None



class LiveClassResponse(LiveClassCreate):

    id: int
    meeting_link: str
    status: str

    class Config:
        from_attributes = True