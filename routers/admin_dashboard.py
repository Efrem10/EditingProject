from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from auth.dependencies import admin_required

from models.user import User
from models.course import Course
from models.lesson import Lesson
from models.enrollment import Enrollment
from models.payment import Payment
from models.certificate import Certificate

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"]
)

@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    total_users = db.query(User).count()

    total_students = db.query(User).filter(
        User.role == "student"
    ).count()

    total_admins = db.query(User).filter(
        User.role == "admin"
    ).count()

    total_courses = db.query(Course).count()

    total_lessons = db.query(Lesson).count()

    total_enrollments = db.query(Enrollment).count()

    total_certificates = db.query(Certificate).count()

    successful_payments = db.query(Payment).filter(
        Payment.status == "success"
    ).count()

    revenue = (
        db.query(func.sum(Payment.amount))
        .filter(Payment.status == "success")
        .scalar()
    )

    if revenue is None:
        revenue = 0

    return {
        "users": total_users,
        "students": total_students,
        "admins": total_admins,
        "courses": total_courses,
        "lessons": total_lessons,
        "enrollments": total_enrollments,
        "payments": successful_payments,
        "certificates": total_certificates,
        "total_revenue": revenue
    }