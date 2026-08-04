from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

import firebase_config

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


# ==================================================
# FIREBASE INITIALIZATION
# ==================================================

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-service-account.json")
    firebase_admin.initialize_app(cred)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ==================================================
# CURRENT USER
# ==================================================

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ==================================================
# REGISTER
# ==================================================

@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):

    existing = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already exists",
        )

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hash_password(user.password),
        role="student",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ==================================================
# EMAIL LOGIN
# ==================================================

@router.post(
    "/login",
    response_model=Token,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    db_user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    if db_user.password is None:
        raise HTTPException(
            status_code=401,
            detail="This account uses Google Sign-In.",
        )

    if not verify_password(
        form_data.password,
        db_user.password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(
        data={
            "sub": db_user.email,
            "user_id": db_user.id,
            "role": db_user.role,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ==================================================
# GOOGLE LOGIN (FIREBASE)
# ==================================================

@router.post(
    "/google",
    response_model=Token,
)
def google_login(
    data: GoogleLogin,
    db: Session = Depends(get_db),
):

    try:
        decoded_token = firebase_auth.verify_id_token(
            data.id_token
        )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Firebase token",
        )

    email = decoded_token.get("email")

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Email not found in token",
        )

    full_name = decoded_token.get(
        "name",
        "Google User",
    )

    firebase_uid = decoded_token.get("uid")

    profile_picture = decoded_token.get("picture")


    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:

        user = User(
            full_name=full_name,
            email=email,
            password=None,
            role="student",
            google_id=firebase_uid,
            profile_picture=profile_picture,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    else:

        changed = False

        if not user.google_id:
            user.google_id = firebase_uid
            changed = True

        if profile_picture and user.profile_picture != profile_picture:
            user.profile_picture = profile_picture
            changed = True

        if full_name and user.full_name != full_name:
            user.full_name = full_name
            changed = True

        if changed:
            db.commit()
            db.refresh(user)

    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }