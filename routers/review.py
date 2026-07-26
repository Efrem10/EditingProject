from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db

from auth.dependencies import get_current_user

from models.review import Review
from models.course import Course
from models.enrollment import Enrollment

from schemas.review import (
    ReviewCreate,
    ReviewResponse
)

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)

@router.post(
    "/course/{course_id}",
    response_model=ReviewResponse
)
def create_review(
    course_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["id"],
        Enrollment.course_id == course_id,
        Enrollment.status == "active"
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="You must enroll before reviewing."
        )

    existing = db.query(Review).filter(
        Review.user_id == current_user["id"],
        Review.course_id == course_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You have already reviewed this course."
        )

    if review.rating < 1 or review.rating > 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5."
        )

    new_review = Review(
        rating=review.rating,
        comment=review.comment,
        user_id=current_user["id"],
        course_id=course_id
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review

@router.get("/course/{course_id}")
def get_course_reviews(
    course_id: int,
    db: Session = Depends(get_db)
):

    reviews = db.query(Review).filter(
        Review.course_id == course_id
    ).all()

    average_rating = (
        db.query(func.avg(Review.rating))
        .filter(Review.course_id == course_id)
        .scalar()
    )

    return {
        "average_rating": round(average_rating, 2) if average_rating else 0,
        "total_reviews": len(reviews),
        "reviews": reviews
    }