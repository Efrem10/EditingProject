from pydantic import BaseModel


class ReviewCreate(BaseModel):
    rating: int
    comment: str


class ReviewResponse(BaseModel):
    id: int
    rating: int
    comment: str
    user_id: int
    course_id: int

    class Config:
        from_attributes = True