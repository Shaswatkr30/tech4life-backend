from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Hospital
from app.schemas import (
    HospitalCreate,
    HospitalResponse,
    HospitalLogin,
    TokenResponse
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_hospital
)


router = APIRouter(
    prefix="/api/hospitals",
    tags=["Hospitals"]
)


# ============================================================
# HOSPITAL REGISTRATION
# ============================================================

@router.post(
    "/register",
    response_model=dict
)
def register_hospital(
    hospital: HospitalCreate,
    db: Session = Depends(get_db)
):

    # Check existing email
    existing_hospital = db.query(Hospital).filter(
        Hospital.email == hospital.email
    ).first()

    if existing_hospital:
        raise HTTPException(
            status_code=400,
            detail="Hospital with this email already exists"
        )

    # Create hospital
    new_hospital = Hospital(
        name=hospital.name,
        address=hospital.address,
        city=hospital.city,
        state=hospital.state,
        phone=hospital.phone,
        email=hospital.email,
        latitude=hospital.latitude,
        longitude=hospital.longitude,

        # Password is stored securely
        password_hash=hash_password(
            hospital.password
        ),

        # IMPORTANT:
        # New hospital requires admin approval
        is_active=False
    )

    db.add(new_hospital)
    db.commit()
    db.refresh(new_hospital)

    return {
        "message": "Hospital registration submitted successfully",
        "hospital_id": new_hospital.id,
        "status": "pending",
        "detail": "Your hospital will become active after admin approval."
    }


# ============================================================
# HOSPITAL LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_hospital(
    hospital: HospitalLogin,
    db: Session = Depends(get_db)
):

    # Find hospital
    existing_hospital = db.query(Hospital).filter(
        Hospital.email == hospital.email
    ).first()

    if not existing_hospital:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Check password
    if not verify_password(
        hospital.password,
        existing_hospital.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # IMPORTANT:
    # Hospital cannot login until admin approves it
    if not existing_hospital.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your hospital registration is pending admin approval"
        )

    # Create JWT token
    access_token = create_access_token({
        "hospital_id": existing_hospital.id
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============================================================
# GET ALL HOSPITALS
# ============================================================

@router.get(
    "/",
    response_model=list[HospitalResponse]
)
def get_hospitals(
    db: Session = Depends(get_db)
):

    hospitals = db.query(Hospital).filter(
        Hospital.is_active == True
    ).all()

    return hospitals


# ============================================================
# GET CURRENT HOSPITAL
# ============================================================

@router.get(
    "/me",
    response_model=HospitalResponse
)
def get_current_hospital_profile(
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    hospital = db.query(Hospital).filter(
        Hospital.id == hospital_id
    ).first()

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    return hospital


# ============================================================
# GET HOSPITAL BY ID
# ============================================================

@router.get(
    "/{hospital_id}",
    response_model=HospitalResponse
)
def get_hospital(
    hospital_id: int,
    db: Session = Depends(get_db)
):

    hospital = db.query(Hospital).filter(
        Hospital.id == hospital_id,
        Hospital.is_active == True
    ).first()

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    return hospital