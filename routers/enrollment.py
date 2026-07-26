from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db

from models.enrollment import Enrollment
from models.course import Course

from schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse
)

from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"]
)

@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED
)
def enroll_course(
    enrollment: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    course = db.query(Course).filter(
        Course.id == enrollment.course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    existing = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["id"],
        Enrollment.course_id == enrollment.course_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already enrolled"
        )

    new_enrollment = Enrollment(
        user_id=current_user["id"],
        course_id=enrollment.course_id
    )

    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)

    return new_enrollment

@router.get("/my-courses")
def my_courses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user["id"],
            Enrollment.status == "active"
        )
        .all()
    )

    courses = []

    for enrollment in enrollments:
        course = db.query(Course).filter(
            Course.id == enrollment.course_id
        ).first()

        if course:
            courses.append(course)

    return courses
@router.get("/my")
def my_courses(
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    return db.query(Enrollment).filter(
        Enrollment.student_id==current_user["id"]
    ).all()