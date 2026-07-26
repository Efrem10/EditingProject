from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from database import get_db

from auth.dependencies import get_current_user

from models.certificate import Certificate
from models.course import Course
from models.lesson import Lesson
from models.progress import Progress
from models.purchase import Purchase


router = APIRouter(
    prefix="/certificate",
    tags=["Certificates"]
)


@router.post("/generate/{course_id}")
def generate_certificate(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # Check course
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found."
        )

    # Admin can generate certificates without purchase check
    if current_user["role"] != "admin":

        purchase = db.query(Purchase).filter(
            Purchase.user_id == current_user["id"],
            Purchase.course_id == course_id,
            Purchase.payment_status == True
        ).first()

        if not purchase:
            raise HTTPException(
                status_code=403,
                detail="You must purchase this course first."
            )

    total_lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).count()

    if total_lessons == 0:
        raise HTTPException(
            status_code=400,
            detail="This course has no lessons."
        )

    completed_lessons = (
        db.query(Progress)
        .join(Lesson, Progress.lesson_id == Lesson.id)
        .filter(
            Progress.user_id == current_user["id"],
            Lesson.course_id == course_id,
            Progress.completed == True
        )
        .count()
    )

    if completed_lessons < total_lessons:
        raise HTTPException(
            status_code=400,
            detail=f"Course not completed. Progress: {completed_lessons}/{total_lessons} lessons."
        )

    existing = db.query(Certificate).filter(
        Certificate.user_id == current_user["id"],
        Certificate.course_id == course_id
    ).first()

    if existing:
        return {
            "message": "Certificate already exists.",
            "certificate_number": existing.certificate_number,
            "verification_code": existing.verification_code
        }

    certificate = Certificate(
        user_id=current_user["id"],
        course_id=course_id,
        certificate_number=f"EDP-{uuid4().hex[:10].upper()}",
        verification_code=uuid4().hex.upper()
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    return {
        "message": "Certificate generated successfully.",
        "certificate_number": certificate.certificate_number,
        "verification_code": certificate.verification_code
    }