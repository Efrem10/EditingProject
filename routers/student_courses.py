from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth.dependencies import get_current_user

from models.payment import Payment


router = APIRouter(
    prefix="/student",
    tags=["Student Courses"]
)


@router.get("/courses")
def my_courses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    payments = (
        db.query(Payment)
        .filter(
            Payment.user_id == current_user["id"],
            Payment.status == "success"
        )
        .all()
    )

    courses = []

    for payment in payments:
        courses.append({
            "course_id": payment.course.id,
            "title": payment.course.title,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "purchased_at": payment.paid_at
        })

    return {
        "total_courses": len(courses),
        "courses": courses
    }