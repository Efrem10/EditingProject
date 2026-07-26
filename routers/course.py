from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models.course import Course
from schemas.course import CourseCreate, CourseResponse
from auth.dependencies import admin_required
from fastapi import UploadFile, File
import os
import shutil

from schemas.course import (
    CourseResponse,
    CourseCreate,
    CourseDetailResponse,
)

router = APIRouter(
    prefix="/course",
    tags=["Course"]
)


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
            # Uncomment if your Course model has this column
            created_by=current_user["id"]
        )

        db.add(new_course)
        db.commit()
        db.refresh(new_course)

        return new_course

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course."
        )
@router.post("/{course_id}/thumbnail")
def upload_thumbnail(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    os.makedirs("uploads/thumbnails", exist_ok=True)

    filename = f"{course_id}_{file.filename}"
    filepath = os.path.join("uploads", "thumbnails", filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    course.thumbnail = f"/uploads/thumbnails/{filename}"

    db.commit()
    db.refresh(course)

    return {
        "message": "Thumbnail uploaded successfully",
        "thumbnail": course.thumbnail
    }        
    
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
            status_code=404,
            detail="Course not found"
        )

    return course    

@router.get(
    "/",
    response_model=list[CourseResponse]
)
def get_courses(
    db: Session = Depends(get_db)
):
    courses = db.query(Course).all()
    return courses

@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):

    db_course = db.query(Course).filter(Course.id == course_id).first()

    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    db_course.title = course.title
    db_course.description = course.description
    db_course.price = course.price
    db_course.category = course.category

    db.commit()
    db.refresh(db_course)

    return db_course

@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()

    return {
        "message": "Course deleted successfully"
    }