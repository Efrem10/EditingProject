from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.purchase import Purchase
from models.course import Course
from models.user import User
from auth.dependencies import get_current_user


router = APIRouter(
    prefix="/purchases",
    tags=["Purchases"]
)


@router.post("/course/{course_id}")
def purchase_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    course = db.query(Course).filter(
        Course.id == course_id
    ).first()


    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )


    existing_purchase = db.query(Purchase).filter(
        Purchase.user_id == current_user["id"],
        Purchase.course_id == course_id
    ).first()


    if existing_purchase:
        raise HTTPException(
            status_code=400,
            detail="Already purchased"
        )


    purchase = Purchase(
        user_id=current_user["id"],
        course_id=course.id,
        amount=course.price,
        payment_status=True
    )


    db.add(purchase)
    db.commit()
    db.refresh(purchase)


    return {
        "message": "Course unlocked successfully",
        "course_id": course.id
    }
@router.get("/my-courses")
def my_courses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    purchases = (
        db.query(Purchase)
        .join(Course, Purchase.course_id == Course.id)
        .filter(
            Purchase.user_id == current_user["id"],
            Purchase.payment_status == True
        )
        .all()
    )

    result = []

    for purchase in purchases:

        result.append({
            "purchase_id": purchase.id,
            "course_id": purchase.course.id,
            "title": purchase.course.title,
            "description": purchase.course.description,
            "price": purchase.course.price,
            "thumbnail": purchase.course.thumbnail,
            "purchased_at": purchase.purchased_at
        })

    return result    