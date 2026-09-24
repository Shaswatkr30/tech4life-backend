import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pwdlib import PasswordHash


load_dotenv()


# ============================================================
# JWT CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "tech4life-secret-key-change-this"
)

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60"
    )
)


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str
):
    return password_hash.verify(
        password,
        hashed_password
    )


# ============================================================
# CREATE JWT TOKEN
# ============================================================

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# ============================================================
# HTTP BEARER
# ============================================================

security = HTTPBearer()


# ============================================================
# CURRENT HOSPITAL
# ============================================================

def get_current_hospital(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        hospital_id = payload.get(
            "hospital_id"
        )

        if hospital_id is None:

            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return int(hospital_id)

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


# ============================================================
# CURRENT ADMIN
# ============================================================

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        admin_id = payload.get(
            "admin_id"
        )

        role = payload.get(
            "role"
        )

        if admin_id is None or role != "admin":

            raise HTTPException(
                status_code=401,
                detail="Invalid admin token"
            )

        return int(admin_id)

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired admin token"
        )