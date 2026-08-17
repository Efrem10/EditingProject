import os
import shutil
import tempfile

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

from database import get_db

from models.lesson import Lesson
from models.course import Course
from models.section import Section
from models.purchase import Purchase

from schemas.lesson import (
    LessonCreate,
    LessonResponse,
)

from auth.dependencies import (
    admin_required,
    SECRET_KEY,
    ALGORITHM,
)

from utils.cloudinary_upload import (
    upload_video_to_cloudinary,
    delete_video_from_cloudinary,
)


# ============================================================
# OPTIONAL CURRENT USER
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
):
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("user_id")
        email = payload.get("sub")
        role = payload.get("role")

        if not user_id or not email:
            return None

        return {
            "id": user_id,
            "email": email,
            "role": role,
        }

    except JWTError:
        return None

    except Exception:
        return None


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/lesson",
    tags=["Lessons"],
)


# ============================================================
# CREATE SECTION
#
# POST /lesson/course/{course_id}/sections
# ============================================================

@router.post(
    "/course/{course_id}/sections",
    status_code=status.HTTP_201_CREATED,
)
def create_section(
    course_id: int,
    section_number: int,
    title: str,
    description: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    if section_number < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section number must be greater than 0.",
        )

    if not title or not title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section title is required.",
        )

    existing_section = (
        db.query(Section)
        .filter(
            Section.course_id == course_id,
            Section.section_number == section_number,
        )
        .first()
    )

    if existing_section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This section number already exists "
                "for this course."
            ),
        )

    new_section = Section(
        course_id=course_id,
        section_number=section_number,
        title=title.strip(),
        description=(
            description.strip()
            if description
            else None
        ),
    )

    try:

        db.add(new_section)
        db.commit()
        db.refresh(new_section)

        return new_section

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "CREATE SECTION ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create section.",
        )


# ============================================================
# GET COURSE SECTIONS
#
# GET /lesson/course/{course_id}/sections
# ============================================================

@router.get(
    "/course/{course_id}/sections",
)
def get_course_sections(
    course_id: int,
    db: Session = Depends(get_db),
):

    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    sections = (
        db.query(Section)
        .filter(
            Section.course_id == course_id,
        )
        .order_by(
            Section.section_number.asc(),
        )
        .all()
    )

    return sections


# ============================================================
# CREATE LESSON
#
# POST /lesson/section/{section_id}
#
# JSON:
#
# {
#     "title": "Introduction to Django",
#     "duration": "07:30",
#     "description": "Introduction...",
#     "is_free": false
# }
#
# section_id comes from URL.
# lesson_number is generated automatically.
# ============================================================

@router.post(
    "/section/{section_id}",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    section_id: int,
    lesson: LessonCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    # --------------------------------------------------------
    # CHECK SECTION
    # --------------------------------------------------------

    section = (
        db.query(Section)
        .filter(
            Section.id == section_id,
        )
        .first()
    )

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found.",
        )

    # --------------------------------------------------------
    # CHECK COURSE
    # --------------------------------------------------------

    course = (
        db.query(Course)
        .filter(
            Course.id == section.course_id,
        )
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    # --------------------------------------------------------
    # VALIDATE TITLE
    # --------------------------------------------------------

    title = (
        lesson.title.strip()
        if lesson.title
        else ""
    )

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson title is required.",
        )

    # --------------------------------------------------------
    # AUTOMATIC LESSON NUMBER
    # --------------------------------------------------------

    last_lesson = (
        db.query(Lesson)
        .filter(
            Lesson.section_id == section_id,
        )
        .order_by(
            Lesson.lesson_number.desc(),
        )
        .first()
    )

    if last_lesson:
        lesson_number = (
            last_lesson.lesson_number + 1
        )
    else:
        lesson_number = 1

    # --------------------------------------------------------
    # CREATE LESSON
    # --------------------------------------------------------

    new_lesson = Lesson(
        course_id=section.course_id,
        section_id=section_id,
        title=title,
        duration=lesson.duration,
        is_free=bool(lesson.is_free),
        lesson_number=lesson_number,
    )

    try:

        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)

        print(
            "LESSON CREATED:",
            new_lesson.id,
            new_lesson.title,
            "SECTION:",
            new_lesson.section_id,
            "NUMBER:",
            new_lesson.lesson_number,
        )

        return new_lesson

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "CREATE LESSON ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lesson.",
        )


# ============================================================
# GET LESSONS FOR SECTION
#
# GET /lesson/section/{section_id}/lessons
# ============================================================

@router.get(
    "/section/{section_id}/lessons",
)
def get_section_lessons(
    section_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):

    section = (
        db.query(Section)
        .filter(
            Section.id == section_id,
        )
        .first()
    )

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found.",
        )

    lessons = (
        db.query(Lesson)
        .filter(
            Lesson.section_id == section_id,
        )
        .order_by(
            Lesson.lesson_number.asc(),
        )
        .all()
    )

    purchase = None

    if current_user:

        purchase = (
            db.query(Purchase)
            .filter(
                Purchase.user_id == current_user["id"],
                Purchase.course_id == section.course_id,
                Purchase.payment_status == True,
            )
            .first()
        )

    result = []

    for lesson in lessons:

        is_admin = (
            current_user
            and current_user.get("role") == "admin"
        )

        if is_admin:
            locked = False
        elif lesson.is_free:
            locked = False
        elif purchase:
            locked = False
        else:
            locked = True

        result.append({

            "id": lesson.id,

            "title": lesson.title,

            "duration": lesson.duration,


            "video_url": (
                lesson.video_url
                if not locked
                else None
            ),

            "is_free": lesson.is_free,

            "locked": locked,

            "course_id": lesson.course_id,

            "section_id": lesson.section_id,

            "lesson_number": lesson.lesson_number,

            "cloudinary_public_id": (
                lesson.cloudinary_public_id
                if is_admin
                else None
            ),
        })

    return result


# ============================================================
# GET COMPLETE COURSE STRUCTURE
#
# GET /lesson/course/{course_id}
# ============================================================

@router.get(
    "/course/{course_id}",
)
def get_course_lessons(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):

    course = (
        db.query(Course)
        .filter(
            Course.id == course_id,
        )
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    purchase = None

    if current_user:

        purchase = (
            db.query(Purchase)
            .filter(
                Purchase.user_id == current_user["id"],
                Purchase.course_id == course_id,
                Purchase.payment_status == True,
            )
            .first()
        )

    sections = (
        db.query(Section)
        .filter(
            Section.course_id == course_id,
        )
        .order_by(
            Section.section_number.asc(),
        )
        .all()
    )

    result = []

    for section in sections:

        lessons = (
            db.query(Lesson)
            .filter(
                Lesson.section_id == section.id,
            )
            .order_by(
                Lesson.lesson_number.asc(),
            )
            .all()
        )

        lessons_result = []

        for lesson in lessons:

            is_admin = (
                current_user
                and current_user.get("role") == "admin"
            )

            if is_admin:
                locked = False
            elif lesson.is_free:
                locked = False
            elif purchase:
                locked = False
            else:
                locked = True

            lessons_result.append({

                "id": lesson.id,

                "title": lesson.title,

                "duration": lesson.duration,

               

                "video_url": (
                    lesson.video_url
                    if not locked
                    else None
                ),

                "is_free": lesson.is_free,

                "locked": locked,

                "course_id": lesson.course_id,

                "section_id": lesson.section_id,

                "lesson_number": lesson.lesson_number,

            })

        result.append({

            "id": section.id,

            "section_number": section.section_number,

            "title": section.title,

            "description": section.description,

            "course_id": section.course_id,

            "lessons": lessons_result,

        })

    return {

        "course_id": course.id,

        "sections": result,

    }


# ============================================================
# WATCH LESSON
#
# GET /lesson/{lesson_id}/watch
# ============================================================

@router.get(
    "/{lesson_id}/watch",
)
def watch_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):

    lesson = (
        db.query(Lesson)
        .filter(
            Lesson.id == lesson_id,
        )
        .first()
    )

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found.",
        )

    if not lesson.video_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video is not available for this lesson.",
        )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if (
        current_user
        and current_user.get("role") == "admin"
    ):

        return {
            "id": lesson.id,
            "title": lesson.title,
            "video_url": lesson.video_url,
            "is_free": lesson.is_free,
            "locked": False,
            "section_id": lesson.section_id,
            "lesson_number": lesson.lesson_number,
        }

    # --------------------------------------------------------
    # FREE
    # --------------------------------------------------------

    if lesson.is_free:

        return {
            "id": lesson.id,
            "title": lesson.title,
            "video_url": lesson.video_url,
            "is_free": True,
            "locked": False,
            "section_id": lesson.section_id,
            "lesson_number": lesson.lesson_number,
        }

    # --------------------------------------------------------
    # LOGIN REQUIRED
    # --------------------------------------------------------

    if not current_user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please login to watch this lesson.",
        )

    # --------------------------------------------------------
    # PURCHASE
    # --------------------------------------------------------

    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.user_id == current_user["id"],
            Purchase.course_id == lesson.course_id,
            Purchase.payment_status == True,
        )
        .first()
    )

    if not purchase:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must purchase this course first.",
        )

    return {
        "id": lesson.id,
        "title": lesson.title,
        "video_url": lesson.video_url,
        "is_free": False,
        "locked": False,
        "section_id": lesson.section_id,
        "lesson_number": lesson.lesson_number,
    }


# ============================================================
# UPLOAD LESSON VIDEO
#
# POST /lesson/lessons/{lesson_id}/upload-video
#
# Form-data:
# file = video
# ============================================================

@router.post(
    "/lessons/{lesson_id}/upload-video",
)
async def upload_lesson_video(
    lesson_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    # --------------------------------------------------------
    # FIND LESSON
    # --------------------------------------------------------

    lesson = (
        db.query(Lesson)
        .filter(
            Lesson.id == lesson_id,
        )
        .first()
    )

    if not lesson:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found.",
        )

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No video selected.",
        )

    # --------------------------------------------------------
    # CHECK VIDEO TYPE
    # --------------------------------------------------------

    if (
        not file.content_type
        or not file.content_type.startswith("video/")
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid video type. "
                "Please upload a valid video file."
            ),
        )

    temp_path = None

    try:

        # ----------------------------------------------------
        # CREATE TEMPORARY FILE
        # ----------------------------------------------------

        suffix = os.path.splitext(
            file.filename
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                file.file,
                temp_file,
            )

        print(
            "TEMP VIDEO:",
            temp_path,
        )

        # ----------------------------------------------------
        # OLD CLOUDINARY PUBLIC ID
        # ----------------------------------------------------

        old_public_id = (
            lesson.cloudinary_public_id
        )

        # ----------------------------------------------------
        # UPLOAD TO CLOUDINARY
        # ----------------------------------------------------

        result = upload_video_to_cloudinary(
            temp_path,
        )

        if not result:

            raise Exception(
                "Cloudinary returned an empty response."
            )

        new_video_url = result.get(
            "secure_url"
        )

        new_public_id = result.get(
            "public_id"
        )

        if not new_video_url:

            raise Exception(
                "Cloudinary did not return secure_url."
            )

        if not new_public_id:

            raise Exception(
                "Cloudinary did not return public_id."
            )

        # ----------------------------------------------------
        # SAVE DATABASE
        # ----------------------------------------------------

        lesson.video_url = new_video_url

        lesson.cloudinary_public_id = (
            new_public_id
        )

        db.commit()

        db.refresh(lesson)

        # ----------------------------------------------------
        # DELETE OLD CLOUDINARY VIDEO
        # ----------------------------------------------------

        if (
            old_public_id
            and old_public_id != new_public_id
        ):

            try:

                delete_video_from_cloudinary(
                    old_public_id,
                )

            except Exception as e:

                print(
                    "OLD VIDEO DELETE ERROR:",
                    repr(e),
                )

        print(
            "VIDEO SAVED:",
            lesson.video_url,
        )

        return {

            "message":
                "Lesson video uploaded successfully.",

            "lesson_id":
                lesson.id,

            "video_url":
                lesson.video_url,

            "public_id":
                lesson.cloudinary_public_id,

        }

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "LESSON VIDEO DATABASE ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save lesson video.",
        )

    except Exception as e:

        db.rollback()

        print(
            "LESSON VIDEO UPLOAD ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload lesson video: {str(e)}",
        )

    finally:

        # ----------------------------------------------------
        # DELETE TEMPORARY FILE
        # ----------------------------------------------------

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            try:
                os.remove(temp_path)

            except Exception as e:

                print(
                    "TEMP VIDEO DELETE ERROR:",
                    repr(e),
                )

        try:
            await file.close()

        except Exception:
            pass


# ============================================================
# DELETE LESSON
#
# DELETE /lesson/lessons/{lesson_id}
# ============================================================

@router.delete(
    "/lessons/{lesson_id}",
)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    lesson = (
        db.query(Lesson)
        .filter(
            Lesson.id == lesson_id,
        )
        .first()
    )

    if not lesson:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found.",
        )

    old_public_id = (
        lesson.cloudinary_public_id
    )

    try:

        db.delete(lesson)

        db.commit()

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "DELETE LESSON ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lesson.",
        )

    # --------------------------------------------------------
    # DELETE CLOUDINARY VIDEO
    # --------------------------------------------------------

    if old_public_id:

        try:

            delete_video_from_cloudinary(
                old_public_id,
            )

        except Exception as e:

            print(
                "CLOUDINARY VIDEO DELETE ERROR:",
                repr(e),
            )

    return {

        "message":
            "Lesson deleted successfully.",

        "lesson_id":
            lesson_id,

    }