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

from schemas.section import (
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    SectionDetailResponse,
)

from auth.dependencies import admin_required


router = APIRouter(
    prefix="/section",
    tags=["Sections"],
)


# ============================================================
# CREATE SECTION
#
# POST /section/course/{course_id}
#
# Creates a section inside a specific course.
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
    # CHECK SECTION NUMBER
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
    # CREATE SECTION
    # --------------------------------------------------------

    new_section = Section(
        course_id=course_id,
        section_number=section.section_number,
        title=section.title,
        description=section.description,
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
# GET ALL SECTIONS FOR A COURSE
#
# GET /section/course/{course_id}
#
# Returns sections in section-number order.
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
        .filter(Section.course_id == course_id)
        .order_by(Section.section_number.asc())
        .all()
    )

    return sections


# ============================================================
# GET ONE SECTION
#
# GET /section/{section_id}
#
# Includes lessons belonging to the section.
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
        .filter(Section.id == section_id)
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
        .filter(Section.id == section_id)
        .first()
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found.",
        )

    # --------------------------------------------------------
    # CHECK SECTION NUMBER
    #
    # Prevent duplicate section numbers inside same course.
    # --------------------------------------------------------

    existing_section = (
        db.query(Section)
        .filter(
            Section.course_id == section.course_id,
            Section.section_number == section_data.section_number,
            Section.id != section_id,
        )
        .first()
    )

    if existing_section:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This section number already exists in this course.",
        )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    section.section_number = section_data.section_number
    section.title = section_data.title
    section.description = section_data.description

    try:

        db.commit()

        db.refresh(section)

        return section

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
# DELETE /section/{section_id}
#
# Because Section -> Lesson uses cascade delete,
# deleting a section also deletes its lessons.
# ============================================================

@router.delete("/{section_id}")
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

    return {
        "message": "Section deleted successfully.",
        "section_id": section_id,
    }