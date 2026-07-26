from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth.dependencies import admin_required
from models.user import User

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.get("/students")
def get_students(
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
    ):
    students = db.query(User).filter(User.role == "student").all()

    return students