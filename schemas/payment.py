from pydantic import BaseModel
from datetime import datetime



class PaymentCreate(BaseModel):
    course_id: int
    gateway: str = "simulation"
    payment_method: str = "simulation"

class PaymentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    amount: float
    payment_method: str
    transaction_id: str | None
    status: str
    paid_at: datetime

    class Config:
        from_attributes = True
        
        