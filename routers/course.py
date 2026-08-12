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

from database import get_db

from models.course import Course

from schemas.course import (
    CourseResponse,
    CourseCreate,
    CourseDetailResponse,
)

from auth.dependencies import admin_required

from utils.cloudinary_upload import (
    upload_image_to_cloudinary,
    delete_image_from_cloudinary,
)


router = APIRouter(
    prefix="/course",
    tags=["Course"]
)


# =========================================================
# CREATE COURSE
# =========================================================

@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED
)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    try:

        new_course = Course(
            title=course.title,
            description=course.description,
            price=course.price,
            category=course.category,
            created_by=current_user["id"],
            is_published=False,
        )

        db.add(new_course)
        db.commit()
        db.refresh(new_course)

        return new_course

    except SQLAlchemyError as e:

        db.rollback()

        print("CREATE COURSE ERROR:", e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course."
        )


# =========================================================
# UPLOAD COURSE THUMBNAIL
#
# Uploads the course cover directly to Cloudinary.
#
# Endpoint:
# POST /course/{course_id}/thumbnail
#
# Form-data:
# file = image
# =========================================================

@router.post("/{course_id}/thumbnail")
async def upload_thumbnail(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):

    # -----------------------------------------------------
    # Find course
    # -----------------------------------------------------

    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image selected."
        )

    # -----------------------------------------------------
    # Allow only image files
    # -----------------------------------------------------

    allowed_types = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
    ]

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid image type. "
                "Please upload JPG, JPEG, PNG or WEBP."
            )
        )

    # -----------------------------------------------------
    # Delete old thumbnail from Cloudinary
    # -----------------------------------------------------

    if course.thumbnail_public_id:

        try:

            delete_image_from_cloudinary(
                course.thumbnail_public_id
            )

        except Exception as e:

            print(
                "OLD THUMBNAIL DELETE ERROR:",
                e
            )

    # -----------------------------------------------------
    # Save uploaded file temporarily
    # -----------------------------------------------------

    temp_dir = "temp_uploads"

    import os
    import shutil

    os.makedirs(
        temp_dir,
        exist_ok=True
    )

    safe_filename = os.path.basename(
        file.filename
    )

    temp_path = os.path.join(
        temp_dir,
        safe_filename
    )

    try:

        with open(
            temp_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        # -------------------------------------------------
        # Upload image to Cloudinary
        # -------------------------------------------------

        result = upload_image_to_cloudinary(
            temp_path
        )

        # -------------------------------------------------
        # Save Cloudinary information
        # -------------------------------------------------

        course.thumbnail = result["secure_url"]

        course.thumbnail_public_id = result[
            "public_id"
        ]

        db.commit()
        db.refresh(course)

        return {
            "message": "Course thumbnail uploaded successfully",
            "course_id": course.id,
            "thumbnail": course.thumbnail,
            "thumbnail_public_id": course.thumbnail_public_id,
        }

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "THUMBNAIL DATABASE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to save course thumbnail."
        )

    except Exception as e:

        print(
            "THUMBNAIL UPLOAD ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload course thumbnail."
        )

    finally:

        # -------------------------------------------------
        # Delete temporary file
        # -------------------------------------------------

        if os.path.exists(temp_path):

            try:
                os.remove(temp_path)

            except Exception:
                pass


# =========================================================
# GET ONE COURSE
# =========================================================

@router.get(
    "/{course_id}",
    response_model=CourseDetailResponse
)
def get_course(
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

    return course


# =========================================================
# GET ALL COURSES
# =========================================================

@router.get(
    "/",
    response_model=list[CourseResponse]
)
def get_courses(
    db: Session = Depends(get_db)
):

    courses = (
        db.query(Course)
        .order_by(Course.created_at.desc())
        .all()
    )

    return courses


# =========================================================
# UPDATE COURSE
#
# This updates course information.
#
# Thumbnail has a separate endpoint:
# POST /course/{course_id}/thumbnail
# =========================================================

@router.put(
    "/{course_id}",
    response_model=CourseResponse
)
def update_course(
    course_id: int,
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):

    db_course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not db_course:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    db_course.title = course.title
    db_course.description = course.description
    db_course.price = course.price
    db_course.category = course.category

    try:

        db.commit()
        db.refresh(db_course)

        return db_course

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "UPDATE COURSE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to update course."
        )


# =========================================================
# DELETE COURSE
#
# Also deletes the course cover from Cloudinary.
# =========================================================

@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
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

    # -----------------------------------------------------
    # Delete course thumbnail from Cloudinary
    # -----------------------------------------------------

    if course.thumbnail_public_id:

        try:

            delete_image_from_cloudinary(
                course.thumbnail_public_id
            )

        except Exception as e:

            print(
                "COURSE THUMBNAIL DELETE ERROR:",
                e
            )

    # -----------------------------------------------------
    # Delete course from database
    # -----------------------------------------------------

    try:

        db.delete(course)
        db.commit()

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "DELETE COURSE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to delete course."
        )

    return {
        "message": "Course deleted successfully"
    }