from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
)

from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

import os
import shutil

from database import get_db

from models.lesson import Lesson
from models.course import Course
from models.section import Section
from models.purchase import Purchase

from schemas.lesson import (
    LessonCreate,
    LessonResponse,
)

from auth.dependencies import admin_required

from utils.cloudinary_upload import (
    upload_video_to_cloudinary,
    delete_video_from_cloudinary,
)


# =========================================================
# OPTIONAL CURRENT USER
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)


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
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/lesson",
    tags=["Lessons"]
)


# =========================================================
# CREATE SECTION
#
# POST /lesson/course/{course_id}/sections
#
# Example:
# {
#     "section_number": 1,
#     "title": "Introduction to Python",
#     "description": "Learn the fundamentals of Python."
# }
# =========================================================

@router.post(
    "/course/{course_id}/sections",
    status_code=status.HTTP_201_CREATED
)
def create_section(
    course_id: int,
    section_number: int,
    title: str,
    description: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    # -----------------------------------------------------
    # CHECK COURSE
    # -----------------------------------------------------

    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # -----------------------------------------------------
    # CREATE SECTION
    # -----------------------------------------------------

    new_section = Section(
        course_id=course_id,
        section_number=section_number,
        title=title,
        description=description
    )

    db.add(new_section)
    db.commit()
    db.refresh(new_section)

    return new_section


# =========================================================
# GET COURSE SECTIONS
#
# GET /lesson/course/{course_id}/sections
# =========================================================

@router.get("/course/{course_id}/sections")
def get_course_sections(
    course_id: int,
    db: Session = Depends(get_db)
):

    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    sections = (
        db.query(Section)
        .filter(Section.course_id == course_id)
        .order_by(Section.section_number)
        .all()
    )

    return sections


# =========================================================
# CREATE LESSON UNDER SECTION
#
# POST /lesson/section/{section_id}
#
# A lesson now belongs to:
#
# Course
#    ↓
# Section
#    ↓
# Lesson
# =========================================================

@router.post(
    "/section/{section_id}",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED
)
def create_lesson(
    section_id: int,
    lesson: LessonCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    # -----------------------------------------------------
    # FIND SECTION
    # -----------------------------------------------------

    section = (
        db.query(Section)
        .filter(Section.id == section_id)
        .first()
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )

    # -----------------------------------------------------
    # CREATE LESSON
    # -----------------------------------------------------

    new_lesson = Lesson(
        title=lesson.title,
        duration=lesson.duration,
        is_free=lesson.is_free,
        lesson_number=lesson.lesson_number,
        course_id=section.course_id,
        section_id=section_id
    )

    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)

    return new_lesson


# =========================================================
# GET LESSONS FOR ONE SECTION
#
# GET /lesson/section/{section_id}/lessons
# =========================================================

@router.get("/section/{section_id}/lessons")
def get_section_lessons(
    section_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):

    # -----------------------------------------------------
    # FIND SECTION
    # -----------------------------------------------------

    section = (
        db.query(Section)
        .filter(Section.id == section_id)
        .first()
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )

    # -----------------------------------------------------
    # GET LESSONS
    # -----------------------------------------------------

    lessons = (
        db.query(Lesson)
        .filter(Lesson.section_id == section_id)
        .order_by(Lesson.lesson_number)
        .all()
    )

    # -----------------------------------------------------
    # CHECK PURCHASE
    # -----------------------------------------------------

    purchase = None

    if current_user:

        purchase = (
            db.query(Purchase)
            .filter(
                Purchase.user_id == current_user["id"],
                Purchase.course_id == section.course_id,
                Purchase.payment_status == True
            )
            .first()
        )

    # -----------------------------------------------------
    # BUILD RESULT
    # -----------------------------------------------------

    result = []

    for lesson in lessons:

        # ADMIN
        if current_user and current_user.get("role") == "admin":

            locked = False
            video_url = lesson.video_url

        # FREE LESSON
        elif lesson.is_free:

            locked = False
            video_url = lesson.video_url

        # PURCHASED COURSE
        elif purchase:

            locked = False
            video_url = lesson.video_url

        # LOCKED LESSON
        else:

            locked = True
            video_url = None

        result.append({
            "id": lesson.id,
            "title": lesson.title,
            "duration": lesson.duration,
            "video_url": video_url,
            "is_free": lesson.is_free,
            "locked": locked,
            "course_id": lesson.course_id,
            "section_id": lesson.section_id,
            "lesson_number": lesson.lesson_number
        })

    return result


# =========================================================
# GET COMPLETE COURSE STRUCTURE
#
# GET /lesson/course/{course_id}
#
# Returns:
#
# Course
#   Section 1
#       Lesson 1
#       Lesson 2
#
#   Section 2
#       Lesson 1
#       Lesson 2
# =========================================================

@router.get("/course/{course_id}")
def get_course_lessons(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):

    # -----------------------------------------------------
    # CHECK COURSE
    # -----------------------------------------------------

    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # -----------------------------------------------------
    # CHECK PURCHASE
    # -----------------------------------------------------

    purchase = None

    if current_user:

        purchase = (
            db.query(Purchase)
            .filter(
                Purchase.user_id == current_user["id"],
                Purchase.course_id == course_id,
                Purchase.payment_status == True
            )
            .first()
        )

    # -----------------------------------------------------
    # GET SECTIONS
    # -----------------------------------------------------

    sections = (
        db.query(Section)
        .filter(Section.course_id == course_id)
        .order_by(Section.section_number)
        .all()
    )

    result = []

    for section in sections:

        lessons_result = []

        lessons = (
            db.query(Lesson)
            .filter(Lesson.section_id == section.id)
            .order_by(Lesson.lesson_number)
            .all()
        )

        for lesson in lessons:

            # ADMIN
            if current_user and current_user.get("role") == "admin":

                locked = False
                video_url = lesson.video_url

            # FREE LESSON
            elif lesson.is_free:

                locked = False
                video_url = lesson.video_url

            # PURCHASED COURSE
            elif purchase:

                locked = False
                video_url = lesson.video_url

            # LOCKED LESSON
            else:

                locked = True
                video_url = None

            lessons_result.append({
                "id": lesson.id,
                "title": lesson.title,
                "duration": lesson.duration,
                "video_url": video_url,
                "is_free": lesson.is_free,
                "locked": locked,
                "course_id": lesson.course_id,
                "section_id": lesson.section_id,
                "lesson_number": lesson.lesson_number
            })

        result.append({
            "id": section.id,
            "section_number": section.section_number,
            "title": section.title,
            "description": section.description,
            "course_id": section.course_id,
            "lessons": lessons_result
        })

    return {
        "course_id": course.id,
        "sections": result
    }


# =========================================================
# WATCH LESSON
#
# FREE LESSON:
#     No login required.
#
# PAID LESSON:
#     Login + purchase required.
# =========================================================

@router.get("/{lesson_id}/watch")
def watch_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):

    lesson = (
        db.query(Lesson)
        .filter(Lesson.id == lesson_id)
        .first()
    )

    if not lesson:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
            "locked": False,
            "section_id": lesson.section_id,
            "lesson_number": lesson.lesson_number
        }

    # =====================================================
    # FREE LESSON
    # =====================================================

    if lesson.is_free:

        return {
            "title": lesson.title,
            "video_url": lesson.video_url,
            "is_free": True,
            "locked": False,
            "section_id": lesson.section_id,
            "lesson_number": lesson.lesson_number
        }

    # =====================================================
    # PAID LESSON WITHOUT LOGIN
    # =====================================================

    if not current_user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please login to watch this lesson."
        )

    # =====================================================
    # CHECK PURCHASE
    # =====================================================

    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.user_id == current_user["id"],
            Purchase.course_id == lesson.course_id,
            Purchase.payment_status == True
        )
        .first()
    )

    if not purchase:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must purchase this course first."
        )

    # =====================================================
    # PURCHASED USER
    # =====================================================

    return {
        "title": lesson.title,
        "video_url": lesson.video_url,
        "is_free": False,
        "locked": False,
        "section_id": lesson.section_id,
        "lesson_number": lesson.lesson_number
    }


# =========================================================
# UPLOAD VIDEO
#
# POST /lesson/lessons/{lesson_id}/upload-video
# =========================================================

@router.post("/lessons/{lesson_id}/upload-video")
async def upload_lesson_video(
    lesson_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    lesson = (
        db.query(Lesson)
        .filter(Lesson.id == lesson_id)
        .first()
    )

    if not lesson:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    temp_dir = "temp_uploads"

    os.makedirs(
        temp_dir,
        exist_ok=True
    )

    # -----------------------------------------------------
    # SAFE FILE NAME
    # -----------------------------------------------------

    safe_filename = os.path.basename(
        file.filename or "video.mp4"
    )

    temp_path = os.path.join(
        temp_dir,
        safe_filename
    )

    try:

        # -------------------------------------------------
        # SAVE TEMPORARY FILE
        # -------------------------------------------------

        with open(temp_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        # -------------------------------------------------
        # UPLOAD TO CLOUDINARY
        # -------------------------------------------------

        result = upload_video_to_cloudinary(
            temp_path
        )

        # -------------------------------------------------
        # SAVE CLOUDINARY DATA
        # -------------------------------------------------

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

        try:
            await file.close()
        except Exception:
            pass


# =========================================================
# DELETE LESSON
#
# DELETE /lesson/lessons/{lesson_id}
# =========================================================

@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    lesson = (
        db.query(Lesson)
        .filter(Lesson.id == lesson_id)
        .first()
    )

    if not lesson:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # -----------------------------------------------------
    # DELETE CLOUDINARY VIDEO
    # -----------------------------------------------------

    if lesson.cloudinary_public_id:

        try:

            delete_video_from_cloudinary(
                lesson.cloudinary_public_id
            )

        except Exception as e:

            print(
                "CLOUDINARY VIDEO DELETE ERROR:",
                e
            )

    # -----------------------------------------------------
    # DELETE LESSON
    # -----------------------------------------------------

    db.delete(lesson)

    db.commit()

    return {
        "message": "Lesson deleted successfully"
    }