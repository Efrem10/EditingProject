from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db

from models.payment import Payment
from models.course import Course
from models.enrollment import Enrollment

from schemas.payment import (
    PaymentCreate,
    PaymentResponse
)
from schemas.payment_confirm import PaymentConfirmation
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    course = db.query(Course).filter(
        Course.id == payment.course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    
    new_payment = Payment(
        user_id=current_user["id"],
        course_id=payment.course_id,
        amount=course.price,
        gateway=payment.gateway,
        payment_method=payment.payment_method,
        status="pending",
        verified=False,
        transaction_id=str(uuid4())
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return new_payment
@router.post("/{payment_id}/complete")
def complete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user["id"]
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    if payment.status == "success":
        raise HTTPException(
            status_code=400,
            detail="Payment already completed"
        )

    payment.status = "success"
    payment.verified = True

    enrollment = Enrollment(
        user_id=payment.user_id,
        course_id=payment.course_id,
        status="active"
    )

    db.add(enrollment)

    db.commit()

    return {
        "message": "Payment completed successfully",
        "transaction_id": payment.transaction_id
    }
@router.post("/{payment_id}/process")
def process_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
    ):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user["id"]
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    if payment.gateway == "simulation":
        return {
            "message": "Choose the simulation result.",
            "payment_id": payment.id,
            "actions": {
                "success": f"/payments/{payment.id}/complete",
                "fail": f"/payments/{payment.id}/fail"
            }
        }

    return {
        "message": f"{payment.gateway} integration will be added later."
    }    
  
@router.post("/{payment_id}/fail")
def fail_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
    ):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user["id"]
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    payment.status = "failed"
    payment.verified = False

    db.commit()

    return {
        "message": "Payment failed."
    }   
    
@router.post("/confirm")
def confirm_payment(
    request: PaymentConfirmation,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    payment = (
        db.query(Payment)
        .filter(
            Payment.transaction_id == request.transaction_id,
            Payment.user_id == current_user["id"]
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found."
        )

    if payment.status == "success":
        return {
            "message": "Payment already confirmed."
        }

    payment.status = "success"
    payment.verified = True

    db.commit()
    db.refresh(payment)

    return {
        "message": "Payment confirmed successfully.",
        "transaction_id": payment.transaction_id,
        "status": payment.status,
        "verified": payment.verified
    }     