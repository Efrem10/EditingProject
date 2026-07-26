from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth.dependencies import get_current_user

from models.lesson import Lesson
from models.payment import Payment


router = APIRouter(
    prefix="/student",
    tags=["Student Lessons"]
)


@router.get("/lessons/{lesson_id}")
def watch_lesson(
    lesson_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )

    if lesson.is_free:
        return {
            "message": "Free lesson",
            "video_url": lesson.video_url
        }

    payment = db.query(Payment).filter(
        Payment.user_id == current_user["id"],
        Payment.course_id == lesson.course_id,
        Payment.status == "success"
    ).first()

    if not payment:
        raise HTTPException(
            status_code=403,
            detail="Purchase this course first."
        )

    return {
        "message": "Access granted",
        "video_url": lesson.video_url
    }