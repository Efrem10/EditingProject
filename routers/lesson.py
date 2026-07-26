from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil

from database import get_db

from models.lesson import Lesson
from models.course import Course
from models.purchase import Purchase

from schemas.lesson import LessonCreate, LessonResponse

from auth.dependencies import admin_required, get_current_user

from utils.cloudinary_upload import (
    upload_video_to_cloudinary,
    delete_video_from_cloudinary
)


router = APIRouter(
    prefix="/lesson",
    tags=["Lessons"]
)


# ==========================
# CREATE LESSON
# ==========================

@router.post(
    "/{course_id}",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED
)
def create_lesson(
    course_id: int,
    lesson: LessonCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )


    new_lesson = Lesson(
        title=lesson.title,
        duration=lesson.duration,
        is_free=lesson.is_free,
        course_id=course_id
    )


    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)

    return new_lesson



# ==========================
# GET COURSE LESSONS
# ==========================

@router.get("/course/{course_id}")
def get_course_lessons(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).all()


    # Admin sees everything
    if current_user["role"] == "admin":
        return lessons


    purchase = db.query(Purchase).filter(
        Purchase.user_id == current_user["id"],
        Purchase.course_id == course_id,
        Purchase.payment_status == True
    ).first()


    result = []

    for lesson in lessons:

        if purchase or lesson.is_free:

            result.append({
                "id": lesson.id,
                "title": lesson.title,
                "duration": lesson.duration,
                "video_url": lesson.video_url,
                "is_free": lesson.is_free,
                "locked": False
            })

        else:

            result.append({
                "id": lesson.id,
                "title": lesson.title,
                "duration": lesson.duration,
                "video_url": None,
                "is_free": lesson.is_free,
                "locked": True
            })


    return result



# ==========================
# WATCH LESSON
# ==========================

@router.get("/{lesson_id}/watch")
def watch_lesson(
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


    # Admin access
    if current_user["role"] == "admin":
        return {
            "title": lesson.title,
            "video_url": lesson.video_url
        }


    # Free lesson
    if lesson.is_free:
        return {
            "title": lesson.title,
            "video_url": lesson.video_url
        }


    # Check purchase
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


    return {
        "title": lesson.title,
        "video_url": lesson.video_url
    }



# ==========================
# UPLOAD VIDEO
# ==========================

@router.post("/lessons/{lesson_id}/upload-video")
async def upload_lesson_video(
    lesson_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()


    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )


    temp_dir = "temp_uploads"

    os.makedirs(
        temp_dir,
        exist_ok=True
    )


    temp_path = os.path.join(
        temp_dir,
        file.filename
    )


    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )


    result = upload_video_to_cloudinary(
        temp_path
    )


    os.remove(temp_path)


    lesson.video_url = result["secure_url"]
    lesson.cloudinary_public_id = result["public_id"]


    db.commit()
    db.refresh(lesson)


    return {
        "message": "Video uploaded successfully",
        "video_url": lesson.video_url,
        "public_id": lesson.cloudinary_public_id
    }



# ==========================
# DELETE LESSON
# ==========================

@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()


    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )


    if lesson.cloudinary_public_id:

        delete_video_from_cloudinary(
            lesson.cloudinary_public_id
        )


    db.delete(lesson)

    db.commit()


    return {
        "message": "Lesson deleted successfully"
    }