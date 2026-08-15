from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import get_db

from models.section import Section
from models.course import Course
from models.lesson import Lesson

from schemas.section import (
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    SectionDetailResponse,
)

from auth.dependencies import admin_required


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/section",
    tags=["Sections"],
)


# ============================================================
# CREATE SECTION
#
# POST /section/course/{course_id}
# ============================================================

@router.post(
    "/course/{course_id}",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_section(
    course_id: int,
    section: SectionCreate,
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
    # CHECK DUPLICATE SECTION NUMBER
    # --------------------------------------------------------

    existing_section = (
        db.query(Section)
        .filter(
            Section.course_id == course_id,
            Section.section_number == section.section_number,
        )
        .first()
    )

    if existing_section:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This section number already exists in this course.",
        )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    new_section = Section(
        course_id=course_id,
        section_number=section.section_number,
        title=section.title.strip(),
        description=(
            section.description.strip()
            if section.description
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
# GET ALL SECTIONS FOR COURSE
#
# GET /section/course/{course_id}
# ============================================================

@router.get(
    "/course/{course_id}",
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
# GET ONE SECTION
#
# GET /section/{section_id}
#
# Includes lessons.
# ============================================================

@router.get(
    "/{section_id}",
    response_model=SectionDetailResponse,
)
def get_section(
    section_id: int,
    db: Session = Depends(get_db),
):

    section = (
        db.query(Section)
        .filter(
            Section.id == section_id
        )
        .first()
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found.",
        )

    return section


# ============================================================
# UPDATE SECTION
#
# PUT /section/{section_id}
#
# Used by EditCourse.
# ============================================================

@router.put(
    "/{section_id}",
    response_model=SectionResponse,
)
def update_section(
    section_id: int,
    section_data: SectionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    # --------------------------------------------------------
    # FIND SECTION
    # --------------------------------------------------------

    section = (
        db.query(Section)
        .filter(
            Section.id == section_id
        )
        .first()
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found.",
        )

    # --------------------------------------------------------
    # CHECK SECTION NUMBER
    # --------------------------------------------------------

    if section_data.section_number is not None:

        existing_section = (
            db.query(Section)
            .filter(
                Section.course_id == section.course_id,

                Section.section_number ==
                section_data.section_number,

                Section.id != section_id,
            )
            .first()
        )

        if existing_section:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This section number already exists "
                    "in this course."
                ),
            )

        section.section_number = (
            section_data.section_number
        )

    # --------------------------------------------------------
    # UPDATE TITLE
    # --------------------------------------------------------

    if section_data.title is not None:

        title = section_data.title.strip()

        if not title:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Section title cannot be empty.",
            )

        section.title = title

    # --------------------------------------------------------
    # UPDATE DESCRIPTION
    # --------------------------------------------------------

    if section_data.description is not None:

        description = (
            section_data.description.strip()
        )

        section.description = (
            description
            if description
            else None
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    try:

        db.commit()

        db.refresh(section)

        return section

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "UPDATE SECTION ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update section.",
        )


# ============================================================
# DELETE SECTION
#
# DELETE /section/{section_id}
#
# Deletes the section and its lessons.
# ============================================================

@router.delete(
    "/{section_id}"
)
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required),
):

    # --------------------------------------------------------
    # FIND SECTION
    # --------------------------------------------------------

    section = (
        db.query(Section)
        .filter(
            Section.id == section_id
        )
        .first()
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found.",
        )

    try:

        # ----------------------------------------------------
        # DELETE LESSONS FIRST
        #
        # This makes deletion reliable even if the database
        # does not have ON DELETE CASCADE configured.
        # ----------------------------------------------------

        lessons = (
            db.query(Lesson)
            .filter(
                Lesson.section_id == section_id
            )
            .all()
        )

        for lesson in lessons:

            db.delete(lesson)

        # ----------------------------------------------------
        # DELETE SECTION
        # ----------------------------------------------------

        db.delete(section)

        db.commit()

    except SQLAlchemyError as e:

        db.rollback()

        print(
            "DELETE SECTION ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete section.",
        )

    return {
        "message": "Section deleted successfully.",
        "section_id": section_id,
    }