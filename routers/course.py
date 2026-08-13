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
from models.section import Section

from schemas.course import (
    CourseResponse,
    CourseCreate,
    CourseDetailResponse,
    SectionResponse,
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
            detailed_description=course.detailed_description,
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

        print(
            "CREATE COURSE ERROR:",
            e,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course.",
        )


# ============================================================
# CREATE SECTION
#
# POST /course/{course_id}/sections
#
# Example JSON:
#
# {
#     "section_number": 1,
#     "title": "Introduction",
#     "description": "Introduction to this course."
# }
# ============================================================

@router.post(
    "/{course_id}/sections",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_section(
    course_id: int,
    section: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    # --------------------------------------------------------
    # CHECK COURSE
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
    # READ SECTION DATA
    # --------------------------------------------------------

    section_number = section.get("section_number")
    title = section.get("title")
    description = section.get("description")

    if section_number is None:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="section_number is required.",
        )

    if not title:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section title is required.",
        )

    # --------------------------------------------------------
    # CHECK DUPLICATE SECTION NUMBER
    # --------------------------------------------------------

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
                f"Section {section_number} already exists "
                "in this course."
            ),
        )

    # --------------------------------------------------------
    # CREATE SECTION
    # --------------------------------------------------------

    new_section = Section(
        course_id=course_id,
        section_number=section_number,
        title=title,
        description=description,
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
            e,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create section.",
        )


# ============================================================
# GET COURSE SECTIONS
#
# GET /course/{course_id}/sections
# ============================================================

@router.get(
    "/{course_id}/sections",
    response_model=list[SectionResponse],
)
def get_course_sections(
    course_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # CHECK COURSE
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
    # GET SECTIONS
    # --------------------------------------------------------

    sections = (
        db.query(Section)
        .filter(
            Section.course_id == course_id
        )
        .order_by(
            Section.section_number.asc()
        )
        .all()
    )

    return sections


# ============================================================
# UPDATE SECTION
#
# PUT /course/sections/{section_id}
# ============================================================

@router.put(
    "/sections/{section_id}",
    response_model=SectionResponse,
)
def update_section(
    section_id: int,
    section: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    db_section = (
        db.query(Section)
        .filter(Section.id == section_id)
        .first()
    )

    if not db_section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found.",
        )

    # --------------------------------------------------------
    # UPDATE SECTION NUMBER
    # --------------------------------------------------------

    if section.get("section_number") is not None:

        new_number = section.get(
            "section_number"
        )

        # Check duplicate number
        duplicate = (
            db.query(Section)
            .filter(
                Section.course_id == db_section.course_id,
                Section.section_number == new_number,
                Section.id != section_id,
            )
            .first()
        )

        if duplicate:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Section {new_number} already exists "
                    "in this course."
                ),
            )

        db_section.section_number = new_number

    # --------------------------------------------------------
    # UPDATE TITLE
    # --------------------------------------------------------

    if section.get("title") is not None:

        title = section.get("title")

        if not title.strip():

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Section title cannot be empty.",
            )

        db_section.title = title

    # --------------------------------------------------------
    # UPDATE DESCRIPTION
    # --------------------------------------------------------

    if "description" in section:

        db_section.description = (
            section.get("description")
        )

    try:

        db.commit()

        db.refresh(db_section)

        return db_section

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "UPDATE SECTION ERROR:",
            e,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update section.",
        )


# ============================================================
# DELETE SECTION
#
# DELETE /course/sections/{section_id}
#
# The Section model has:
#
# lessons = relationship(
#     "Lesson",
#     back_populates="section",
#     cascade="all, delete-orphan"
# )
#
# Therefore deleting a section deletes its lessons.
# ============================================================

@router.delete(
    "/sections/{section_id}"
)
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    section = (
        db.query(Section)
        .filter(Section.id == section_id)
        .first()
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found.",
        )

    try:

        db.delete(section)

        db.commit()

        return {
            "message": "Section deleted successfully.",
            "section_id": section_id,
        }

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "DELETE SECTION ERROR:",
            e,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete section.",
        )


# ============================================================
# UPLOAD COURSE THUMBNAIL
#
# POST /course/{course_id}/thumbnail
#
# Form-data:
# file = image
# ============================================================

@router.post(
    "/{course_id}/thumbnail"
)
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

    temp_path = None

    try:

        # ----------------------------------------------------
        # CREATE TEMPORARY FILE
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(
                file.filename
            )[1],
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                file.file,
                temp_file,
            )

        # ----------------------------------------------------
        # UPLOAD TO CLOUDINARY
        # ----------------------------------------------------

        result = upload_image_to_cloudinary(
            temp_path
        )

        if not result:

            raise Exception(
                "Cloudinary returned an empty response."
            )

        new_secure_url = result.get(
            "secure_url"
        )

        new_public_id = result.get(
            "public_id"
        )

        if (
            not new_secure_url
            or not new_public_id
        ):

            raise Exception(
                "Cloudinary upload did not return "
                "secure_url or public_id."
            )

        # ----------------------------------------------------
        # SAVE OLD PUBLIC ID
        # ----------------------------------------------------

        old_public_id = (
            course.thumbnail_public_id
        )

        # ----------------------------------------------------
        # SAVE NEW IMAGE
        # ----------------------------------------------------

        course.thumbnail = new_secure_url

        course.thumbnail_public_id = (
            new_public_id
        )

        db.commit()

        db.refresh(course)

        # ----------------------------------------------------
        # DELETE OLD IMAGE
        # ----------------------------------------------------

        if (
            old_public_id
            and old_public_id != new_public_id
        ):

            try:

                delete_image_from_cloudinary(
                    old_public_id
                )

            except Exception as e:

                print(
                    "OLD THUMBNAIL DELETE ERROR:",
                    e,
                )

        return {
            "message": (
                "Course thumbnail uploaded "
                "successfully."
            ),
            "course_id": course.id,
            "thumbnail": course.thumbnail,
            "thumbnail_public_id": (
                course.thumbnail_public_id
            ),
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
        # DELETE TEMP FILE
        # ----------------------------------------------------

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

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
#
# Returns:
#
# Course
#   ├── description
#   ├── detailed_description
#   ├── sections
#   │     ├── section 1
#   │     │     ├── lesson 1
#   │     │     └── lesson 2
#   │     └── section 2
#   │           ├── lesson 1
#   │           └── lesson 2
#   │
#   └── lessons
#
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
        .order_by(
            Course.created_at.desc()
        )
        .all()
    )

    return courses


# ============================================================
# UPDATE COURSE
#
# PUT /course/{course_id}
#
# Updates:
# - title
# - short description
# - detailed description
# - price
# - category
#
# Thumbnail is updated separately.
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

    db_course.description = (
        course.description
    )

    db_course.detailed_description = (
        course.detailed_description
    )

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
# DELETE /course/{course_id}
#
# Course
#    ↓
# Sections
#    ↓
# Lessons
#
# are removed through the relationships/cascade.
# ============================================================

@router.delete(
    "/{course_id}"
)
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

    thumbnail_public_id = (
        course.thumbnail_public_id
    )

    # --------------------------------------------------------
    # DELETE COURSE
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
    # DELETE CLOUDINARY THUMBNAIL
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