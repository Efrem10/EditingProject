from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth.dependencies import admin_required
from models.settings import Settings
from schemas.settings import SettingsBase

router=APIRouter(
    prefix="/settings",
    tags=["Settings"]
)

@router.get("/")
def get_settings(
    db:Session=Depends(get_db),
    current_user=Depends(admin_required)
):

    settings=db.query(Settings).first()

    if not settings:

        settings=Settings()

        db.add(settings)

        db.commit()

        db.refresh(settings)

    return settings


@router.put("/")
def update_settings(
    data:SettingsBase,
    db:Session=Depends(get_db),
    current_user=Depends(admin_required)
):

    settings=db.query(Settings).first()

    for key,value in data.model_dump().items():

        setattr(settings,key,value)

    db.commit()

    db.refresh(settings)

    return settings