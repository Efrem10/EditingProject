from pydantic import BaseModel


class PaymentConfirmation(BaseModel):
    transaction_id: str