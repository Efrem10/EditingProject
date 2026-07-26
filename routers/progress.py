from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db

from models.course import Course
from models.progress import Progress
from models.lesson import Lesson
from models.purchase import Purchase

from schemas.progress import ProgressResponse

from auth.dependencies import get_current_user


router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)


# ==========================
# MARK LESSON AS COMPLETED
# ==========================

@router.post(
    "/lesson/{lesson_id}",
    response_model=ProgressResponse
)
def complete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )

    # Admin can complete any lesson
    if current_user["role"] != "admin" and not lesson.is_free:

        purchase = db.query(Purchase).filter(
            Purchase.user_id == current_user["id"],
            Purchase.course_id == lesson.course_id,
            Purchase.payment_status == True
        ).first()

        if not purchase:
            raise HTTPException(
                status_code=403,
                detail="You must purchase this course first."
            )

    existing = db.query(Progress).filter(
        Progress.user_id == current_user["id"],
        Progress.lesson_id == lesson_id
    ).first()

    if existing:
        existing.completed = True
        existing.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(existing)

        return existing

    progress = Progress(
        user_id=current_user["id"],
        lesson_id=lesson_id,
        completed=True,
        completed_at=datetime.utcnow()
    )

    db.add(progress)
    db.commit()
    db.refresh(progress)

    return progress


# ==========================
# COURSE PROGRESS
# ==========================

@router.get("/course/{course_id}")
def course_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # Admin can view all course progress
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

    percentage = 0

    if total_lessons > 0:
        percentage = round(
            (completed_lessons / total_lessons) * 100,
            2
        )

    return {
        "course_id": course_id,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress": percentage
    }
    
@router.get("/course/{course_id}/completion")
def course_completion(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

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

    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    total_lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).count()

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

    percentage = 0

    if total_lessons > 0:
        percentage = round(
            (completed_lessons / total_lessons) * 100,
            2
        )

    return {
        "course_id": course.id,
        "course_title": course.title,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "progress": percentage,
        "certificate_eligible": percentage == 100
    }    