from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import uuid4

from database import get_db

from auth.dependencies import admin_required , get_current_user
from models.live_class import LiveClass
from schemas.live_class import LiveClassCreate

router = APIRouter(
    prefix="/live-class",
    tags=["Live Class"]
)

@router.post("/")
def create_live_class(
    data: LiveClassCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    provider = data.meeting_provider.lower()

    if provider == "jitsi":
        meeting_link = f"https://meet.jit.si/{uuid4()}"
    elif provider == "google meet":
        meeting_link = data.meeting_link
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported meeting provider"
        )

    live = LiveClass(
        title=data.title,
        course_id=data.course_id,
        meeting_provider=data.meeting_provider,
        meeting_link=meeting_link,
        scheduled_at=data.scheduled_at,
        description=data.description,
        duration=data.duration,
        status="scheduled"
    )

    db.add(live)
    db.commit()
    db.refresh(live)

    return live

@router.get("/")
def get_live_classes(
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    classes = db.query(LiveClass).order_by(
        LiveClass.scheduled_at.desc()
    ).all()

    return classes
@router.get("/student")
def student_live_classes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(LiveClass).order_by(
        LiveClass.scheduled_at
    ).all()