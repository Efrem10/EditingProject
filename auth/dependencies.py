from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from config import SECRET_KEY, ALGORITHM


# ============================================================
# OAUTH2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:

        # ----------------------------------------------------
        # DECODE TOKEN
        # ----------------------------------------------------

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        print("========================================")
        print("JWT TOKEN VALIDATION")
        print("PAYLOAD:", payload)
        print("SECRET KEY EXISTS:", bool(SECRET_KEY))
        print("ALGORITHM:", ALGORITHM)
        print("========================================")

        # ----------------------------------------------------
        # GET USER DATA
        # ----------------------------------------------------

        user_id = payload.get("user_id")
        email = payload.get("sub")
        role = payload.get("role")

        print("USER ID:", user_id)
        print("EMAIL:", email)
        print("ROLE:", role)

        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        if user_id is None:
            print("JWT ERROR: user_id is missing")
            raise credentials_exception

        if email is None:
            print("JWT ERROR: sub/email is missing")
            raise credentials_exception

        return {
            "id": user_id,
            "email": email,
            "role": role
        }

    except JWTError as e:

        print("========================================")
        print("JWT DECODE ERROR")
        print("ERROR:", repr(e))
        print("========================================")

        raise credentials_exception

    except Exception as e:

        print("========================================")
        print("JWT UNKNOWN ERROR")
        print("ERROR:", repr(e))
        print("========================================")

        raise credentials_exception


# ============================================================
# ADMIN REQUIRED
# ============================================================

def admin_required(
    current_user: dict = Depends(get_current_user)
):

    print("========================================")
    print("ADMIN CHECK")
    print("CURRENT USER:", current_user)
    print("ROLE:", current_user.get("role"))
    print("========================================")

    if current_user.get("role") != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user