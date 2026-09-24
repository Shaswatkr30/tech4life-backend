from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ICUResource, Hospital

from app.schemas import (
    ICUCreate,
    ICUResponse,
    PublicICUResponse
)

from app.auth import get_current_hospital


router = APIRouter(
    prefix="/api/icu",
    tags=["ICU Beds"]
)


# ============================================================
# ADD ICU
# ============================================================

@router.post(
    "/",
    response_model=ICUResponse
)
def add_icu(
    icu: ICUCreate,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    if icu.total_beds < 0:
        raise HTTPException(
            status_code=400,
            detail="Total beds cannot be negative"
        )

    if icu.available_beds < 0:
        raise HTTPException(
            status_code=400,
            detail="Available beds cannot be negative"
        )

    if icu.available_beds > icu.total_beds:
        raise HTTPException(
            status_code=400,
            detail="Available beds cannot exceed total beds"
        )

    existing = db.query(ICUResource).filter(
        ICUResource.hospital_id == hospital_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="ICU resource already exists for this hospital"
        )

    new_icu = ICUResource(
        hospital_id=hospital_id,
        total_beds=icu.total_beds,
        available_beds=icu.available_beds
    )

    db.add(new_icu)
    db.commit()
    db.refresh(new_icu)

    return new_icu


# ============================================================
# GET MY ICU
# ============================================================

@router.get(
    "/my",
    response_model=list[ICUResponse]
)
def get_my_icu(
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    return db.query(ICUResource).filter(
        ICUResource.hospital_id == hospital_id
    ).all()


# ============================================================
# PUBLIC ICU
# ============================================================

@router.get(
    "/public",
    response_model=list[PublicICUResponse]
)
def get_public_icu(
    db: Session = Depends(get_db)
):

    results = db.query(
        ICUResource,
        Hospital
    ).join(
        Hospital,
        ICUResource.hospital_id == Hospital.id
    ).all()

    return [
        {
            "id": icu.id,
            "hospital_id": hospital.id,
            "hospital_name": hospital.name,
            "city": hospital.city,
            "state": hospital.state,
            "total_beds": icu.total_beds,
            "available_beds": icu.available_beds,
            "updated_at": icu.updated_at
        }

        for icu, hospital in results
    ]


# ============================================================
# UPDATE ICU
# ============================================================

@router.put(
    "/{icu_id}",
    response_model=ICUResponse
)
def update_icu(
    icu_id: int,
    icu: ICUCreate,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    resource = db.query(ICUResource).filter(
        ICUResource.id == icu_id,
        ICUResource.hospital_id == hospital_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="ICU resource not found"
        )

    if icu.total_beds < 0:
        raise HTTPException(
            status_code=400,
            detail="Total beds cannot be negative"
        )

    if icu.available_beds < 0:
        raise HTTPException(
            status_code=400,
            detail="Available beds cannot be negative"
        )

    if icu.available_beds > icu.total_beds:
        raise HTTPException(
            status_code=400,
            detail="Available beds cannot exceed total beds"
        )

    resource.total_beds = icu.total_beds
    resource.available_beds = icu.available_beds

    db.commit()
    db.refresh(resource)

    return resource


# ============================================================
# DELETE ICU
# ============================================================

@router.delete("/{icu_id}")
def delete_icu(
    icu_id: int,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    resource = db.query(ICUResource).filter(
        ICUResource.id == icu_id,
        ICUResource.hospital_id == hospital_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="ICU resource not found"
        )

    db.delete(resource)
    db.commit()

    return {
        "message": "ICU resource deleted successfully"
    }