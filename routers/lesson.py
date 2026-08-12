from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os
import shutil

from database import get_db

from models.lesson import Lesson
from models.course import Course
from models.purchase import Purchase

from schemas.lesson import LessonCreate, LessonResponse

from auth.dependencies import admin_required

from utils.cloudinary_upload import (
    upload_video_to_cloudinary,
    delete_video_from_cloudinary
)

# IMPORTANT:
# auto_error=False means a user can access the endpoint
# even when there is NO login token.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)

router = APIRouter(
    prefix="/lesson",
    tags=["Lessons"]
)


# =========================================================
# OPTIONAL CURRENT USER
# =========================================================

def get_optional_user(
    token: str | None = Depends(oauth2_scheme)
):
    """
    Returns the logged-in user when a valid token exists.

    Returns None when:
    - No token was provided
    - Token is invalid
    - Token cannot be decoded

    This allows FREE lessons to be accessed without login.
    """

    if not token:
        return None

    try:
        from auth.dependencies import SECRET_KEY, ALGORITHM

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")
        email = payload.get("sub")
        role = payload.get("role")

        if not user_id or not email:
            return None

        return {
            "id": user_id,
            "email": email,
            "role": role
        }

    except JWTError:
        return None
    except Exception:
        return None


# =========================================================
# CREATE LESSON
# =========================================================

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


# =========================================================
# GET COURSE LESSONS
#
# IMPORTANT:
# LOGIN IS NOT REQUIRED HERE.
#
# Free lesson:
#     Anyone can see it and get video_url.
#
# Locked lesson:
#     Logged-in purchased user -> video_url
#     Logged-in non-purchased -> locked
#     Guest -> locked
# =========================================================

@router.get("/course/{course_id}")
def get_course_lessons(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):

    # Check course
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).all()

    # =====================================================
    # ADMIN
    # =====================================================

    if current_user and current_user.get("role") == "admin":

        return [
            {
                "id": lesson.id,
                "title": lesson.title,
                "duration": lesson.duration,
                "video_url": lesson.video_url,
                "is_free": lesson.is_free,
                "locked": False,
                "course_id": lesson.course_id
            }
            for lesson in lessons
        ]

    # =====================================================
    # CHECK PURCHASE
    # =====================================================

    purchase = None

    if current_user:

        purchase = db.query(Purchase).filter(
            Purchase.user_id == current_user["id"],
            Purchase.course_id == course_id,
            Purchase.payment_status == True
        ).first()

    # =====================================================
    # BUILD RESULT
    # =====================================================

    result = []

    for lesson in lessons:

        # -------------------------------------------------
        # FREE LESSON
        # -------------------------------------------------

        if lesson.is_free:

            result.append({
                "id": lesson.id,
                "title": lesson.title,
                "duration": lesson.duration,
                "video_url": lesson.video_url,
                "is_free": True,
                "locked": False,
                "course_id": lesson.course_id
            })

        # -------------------------------------------------
        # PURCHASED COURSE
        # -------------------------------------------------

        elif purchase:

            result.append({
                "id": lesson.id,
                "title": lesson.title,
                "duration": lesson.duration,
                "video_url": lesson.video_url,
                "is_free": False,
                "locked": False,
                "course_id": lesson.course_id
            })

        # -------------------------------------------------
        # LOCKED LESSON
        # -------------------------------------------------

        else:

            result.append({
                "id": lesson.id,
                "title": lesson.title,
                "duration": lesson.duration,
                "video_url": None,
                "is_free": False,
                "locked": True,
                "course_id": lesson.course_id
            })

    return result


# =========================================================
# WATCH LESSON
#
# FREE LESSONS:
#     No login required.
#
# PAID LESSONS:
#     Login + purchase required.
# =========================================================

@router.get("/{lesson_id}/watch")
def watch_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):

    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )

    # =====================================================
    # ADMIN
    # =====================================================

    if current_user and current_user.get("role") == "admin":

        return {
            "title": lesson.title,
            "video_url": lesson.video_url,
            "is_free": lesson.is_free,
            "locked": False
        }

    # =====================================================
    # FREE LESSON
    # =====================================================

    if lesson.is_free:

        return {
            "title": lesson.title,
            "video_url": lesson.video_url,
            "is_free": True,
            "locked": False
        }

    # =====================================================
    # PAID LESSON WITHOUT LOGIN
    # =====================================================

    if not current_user:

        raise HTTPException(
            status_code=401,
            detail="Please login to watch this lesson."
        )

    # =====================================================
    # CHECK PURCHASE
    # =====================================================

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

    # =====================================================
    # PURCHASED USER
    # =====================================================

    return {
        "title": lesson.title,
        "video_url": lesson.video_url,
        "is_free": False,
        "locked": False
    }


# =========================================================
# UPLOAD VIDEO
# =========================================================

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

    # Make filename safer
    safe_filename = os.path.basename(
        file.filename or "video.mp4"
    )

    temp_path = os.path.join(
        temp_dir,
        safe_filename
    )

    try:

        with open(temp_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        result = upload_video_to_cloudinary(
            temp_path
        )

        lesson.video_url = result["secure_url"]
        lesson.cloudinary_public_id = result["public_id"]

        db.commit()
        db.refresh(lesson)

        return {
            "message": "Video uploaded successfully",
            "video_url": lesson.video_url,
            "public_id": lesson.cloudinary_public_id
        }

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)


# =========================================================
# DELETE LESSON
# =========================================================

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

    # Delete Cloudinary video first
    if lesson.cloudinary_public_id:

        delete_video_from_cloudinary(
            lesson.cloudinary_public_id
        )

    db.delete(lesson)

    db.commit()

    return {
        "message": "Lesson deleted successfully"
    }