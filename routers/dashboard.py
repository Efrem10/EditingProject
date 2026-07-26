from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth.dependencies import get_current_user, admin_required

from models.course import Course
from models.lesson import Lesson
from models.user import User
from models.enrollment import Enrollment
from models.payment import Payment
from models.live_class import LiveClass
from models.progress import Progress

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/student")
def student_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user_id = current_user["id"]

    total_courses = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).count()

    completed_lessons = db.query(Progress).filter(
        Progress.user_id == user_id
    ).count()

    live_classes = db.query(LiveClass).filter(
        LiveClass.status == "scheduled"
    ).count()

    payments = db.query(Payment).filter(
        Payment.user_id == user_id
    ).count()

    return {
        "total_courses": total_courses,
        "completed_lessons": completed_lessons,
        "live_classes": live_classes,
        "payments": payments
    }


@router.get("/admin")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    return {
        "courses": db.query(Course).count(),
        "students": db.query(User).filter(User.role == "student").count(),
        "lessons": db.query(Lesson).count(),
        "payments": db.query(Payment).count(),
        "live_classes": db.query(LiveClass).count()
    }