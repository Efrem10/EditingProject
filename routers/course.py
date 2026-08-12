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
    tags=["Course"],
)


# ============================================================
# CREATE COURSE
# ============================================================

@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
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
            detail="Failed to create course.",
        )


# ============================================================
# UPLOAD COURSE THUMBNAIL
#
# POST /course/{course_id}/thumbnail
#
# Form-data:
# file = image
#
# Image is stored permanently on Cloudinary.
# ============================================================

@router.post("/{course_id}/thumbnail")
async def upload_thumbnail(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    # --------------------------------------------------------
    # FIND COURSE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image selected.",
        )

    # --------------------------------------------------------
    # CHECK CONTENT TYPE
    # --------------------------------------------------------

    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid image type. "
                "Please upload JPG, JPEG, PNG or WEBP."
            ),
        )

    # --------------------------------------------------------
    # CREATE TEMPORARY FILE
    # --------------------------------------------------------

    temp_path = None

    try:

        # Create a temporary file.
        # This avoids depending on a permanent local uploads folder.

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(file.filename)[1],
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                file.file,
                temp_file,
            )

        # ----------------------------------------------------
        # UPLOAD NEW IMAGE TO CLOUDINARY FIRST
        # ----------------------------------------------------

        result = upload_image_to_cloudinary(
            temp_path
        )

        # ----------------------------------------------------
        # VERIFY CLOUDINARY RESULT
        # ----------------------------------------------------

        if not result:

            raise Exception(
                "Cloudinary returned an empty response."
            )

        new_secure_url = result.get("secure_url")
        new_public_id = result.get("public_id")

        if not new_secure_url or not new_public_id:

            raise Exception(
                "Cloudinary upload did not return "
                "secure_url or public_id."
            )

        # ----------------------------------------------------
        # SAVE OLD VALUES
        # ----------------------------------------------------

        old_public_id = course.thumbnail_public_id

        # ----------------------------------------------------
        # SAVE NEW CLOUDINARY URL
        # ----------------------------------------------------

        course.thumbnail = new_secure_url

        course.thumbnail_public_id = new_public_id

        db.commit()

        db.refresh(course)

        # ----------------------------------------------------
        # DELETE OLD CLOUDINARY IMAGE
        #
        # IMPORTANT:
        # We delete the old image ONLY after the new image
        # has successfully uploaded and the database has
        # successfully saved the new URL.
        # ----------------------------------------------------

        if old_public_id and old_public_id != new_public_id:

            try:

                delete_image_from_cloudinary(
                    old_public_id
                )

            except Exception as e:

                print(
                    "OLD THUMBNAIL DELETE ERROR:",
                    e,
                )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return {
            "message": "Course thumbnail uploaded successfully.",
            "course_id": course.id,
            "thumbnail": course.thumbnail,
            "thumbnail_public_id": course.thumbnail_public_id,
        }

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "THUMBNAIL DATABASE ERROR:",
            e,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save course thumbnail.",
        )

    except Exception as e:

        db.rollback()

        print(
            "THUMBNAIL UPLOAD ERROR:",
            e,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload course thumbnail.",
        )

    finally:

        # ----------------------------------------------------
        # DELETE TEMPORARY FILE
        # ----------------------------------------------------

        if temp_path and os.path.exists(temp_path):

            try:

                os.remove(temp_path)

            except Exception as e:

                print(
                    "TEMP FILE DELETE ERROR:",
                    e,
                )

        try:

            await file.close()

        except Exception:

            pass


# ============================================================
# GET ONE COURSE
#
# GET /course/{course_id}
# ============================================================

@router.get(
    "/{course_id}",
    response_model=CourseDetailResponse,
)
def get_course(
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

    return course


# ============================================================
# GET ALL COURSES
#
# GET /course/
# ============================================================

@router.get(
    "/",
    response_model=list[CourseResponse],
)
def get_courses(
    db: Session = Depends(get_db),
):

    courses = (
        db.query(Course)
        .order_by(Course.created_at.desc())
        .all()
    )

    return courses


# ============================================================
# UPDATE COURSE
#
# Thumbnail is updated separately:
#
# POST /course/{course_id}/thumbnail
# ============================================================

@router.put(
    "/{course_id}",
    response_model=CourseResponse,
)
def update_course(
    course_id: int,
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    db_course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not db_course:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    # --------------------------------------------------------
    # UPDATE COURSE INFORMATION
    # --------------------------------------------------------

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
            e,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course.",
        )


# ============================================================
# DELETE COURSE
#
# Also deletes its Cloudinary thumbnail.
# ============================================================

@router.delete("/{course_id}")
def delete_course(
    course_id: int,
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

    # --------------------------------------------------------
    # SAVE CLOUDINARY PUBLIC ID
    # --------------------------------------------------------

    thumbnail_public_id = course.thumbnail_public_id

    # --------------------------------------------------------
    # DELETE DATABASE RECORD
    # --------------------------------------------------------

    try:

        db.delete(course)

        db.commit()

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "DELETE COURSE ERROR:",
            e,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course.",
        )

    # --------------------------------------------------------
    # DELETE CLOUDINARY IMAGE
    #
    # Only after database deletion succeeds.
    # --------------------------------------------------------

    if thumbnail_public_id:

        try:

            delete_image_from_cloudinary(
                thumbnail_public_id
            )

        except Exception as e:

            print(
                "COURSE THUMBNAIL DELETE ERROR:",
                e,
            )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return {
        "message": "Course deleted successfully.",
        "course_id": course_id,
    }