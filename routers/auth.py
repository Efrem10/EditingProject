from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os

from google.oauth2 import id_token
from google.auth.transport import requests

from database import get_db
from models.user import User

from schemas.user import (
    UserCreate,
    UserResponse,
    GoogleLogin,
    Token,
)

from auth.password import hash_password, verify_password
from auth.dependencies import get_current_user
from auth.jwt import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# Google OAuth Client ID from Firebase Console
GOOGLE_CLIENT_ID = os.getenv("657002186776-fb7tdtcqeu6lcbahmap9e2c73omo5589.apps.googleusercontent.com")


if not GOOGLE_CLIENT_ID:
    raise Exception(
        "GOOGLE_CLIENT_ID environment variable is missing"
    )



@router.get("/me")
def get_me(
    current_user: dict = Depends(get_current_user)
):
    return current_user




# ==========================
# NORMAL REGISTER
# ==========================

@router.post(
    "/register",
    response_model=UserResponse
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing = db.query(User).filter(
        User.email == user.email
    ).first()


    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )


    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hash_password(user.password),
        role="student"
    )


    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    return new_user





# ==========================
# NORMAL LOGIN
# ==========================

@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    db_user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )


    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )



    # Google users don't have password
    if db_user.password is None:

        raise HTTPException(
            status_code=401,
            detail="This account uses Google Sign-In."
        )



    if not verify_password(
        form_data.password,
        db_user.password
    ):

        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )



    token = create_access_token(
        data={
            "sub": db_user.email,
            "user_id": db_user.id,
            "role": db_user.role,
        }
    )



    return {
        "access_token": token,
        "token_type": "bearer",
    }






# ==========================
# GOOGLE LOGIN
# ==========================

@router.post(
    "/google",
    response_model=Token
)
def google_login(
    data: GoogleLogin,
    db: Session = Depends(get_db)
):

    try:

        google_user = id_token.verify_oauth2_token(
            data.id_token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )


    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid Google token"
        )



    email = google_user.get("email")

    full_name = google_user.get(
        "name",
        "Google User"
    )

    google_id = google_user.get(
        "sub"
    )

    profile_picture = google_user.get(
        "picture"
    )



    user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )



    # New Google user

    if user is None:


        user = User(

            full_name=full_name,

            email=email,

            password=None,

            role="student",

            google_id=google_id,

            profile_picture=profile_picture

        )


        db.add(user)

        db.commit()

        db.refresh(user)



    # Existing user

    else:


        changed = False



        if not user.google_id:

            user.google_id = google_id

            changed = True



        if profile_picture:

            user.profile_picture = profile_picture

            changed = True



        if changed:

            db.commit()

            db.refresh(user)




    token = create_access_token(

        data={

            "sub": user.email,

            "user_id": user.id,

            "role": user.role,

        }

    )



    return {

        "access_token": token,

        "token_type": "bearer"

    }