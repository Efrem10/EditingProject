from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    course_id: int
    payment_method: str