from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BloodInventory, Hospital

from app.schemas import (
    BloodCreate,
    BloodResponse,
    PublicBloodResponse
)

from app.auth import get_current_hospital


router = APIRouter(
    prefix="/api/blood",
    tags=["Blood Inventory"]
)


ALLOWED_BLOOD_GROUPS = [
    "A+", "A-", "B+", "B-",
    "AB+", "AB-", "O+", "O-"
]


# ============================================================
# ADD BLOOD
# ============================================================

@router.post(
    "/",
    response_model=BloodResponse
)
def add_blood(
    blood: BloodCreate,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    if blood.blood_group not in ALLOWED_BLOOD_GROUPS:
        raise HTTPException(
            status_code=400,
            detail="Invalid blood group"
        )

    if blood.units_available < 0:
        raise HTTPException(
            status_code=400,
            detail="Units cannot be negative"
        )

    existing = db.query(BloodInventory).filter(
        BloodInventory.hospital_id == hospital_id,
        BloodInventory.blood_group == blood.blood_group
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This blood group already exists"
        )

    new_blood = BloodInventory(
        hospital_id=hospital_id,
        blood_group=blood.blood_group,
        units_available=blood.units_available
    )

    db.add(new_blood)
    db.commit()
    db.refresh(new_blood)

    return new_blood


# ============================================================
# GET MY BLOOD
# ============================================================

@router.get(
    "/my",
    response_model=list[BloodResponse]
)
def get_my_blood(
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    return db.query(BloodInventory).filter(
        BloodInventory.hospital_id == hospital_id
    ).all()


# ============================================================
# PUBLIC BLOOD
# ============================================================

@router.get(
    "/public",
    response_model=list[PublicBloodResponse]
)
def get_public_blood(
    db: Session = Depends(get_db)
):

    results = db.query(
        BloodInventory,
        Hospital
    ).join(
        Hospital,
        BloodInventory.hospital_id == Hospital.id
    ).all()

    return [
        {
            "id": blood.id,
            "hospital_id": hospital.id,
            "hospital_name": hospital.name,
            "city": hospital.city,
            "state": hospital.state,
            "blood_group": blood.blood_group,
            "units_available": blood.units_available,
            "updated_at": blood.updated_at
        }

        for blood, hospital in results
    ]


# ============================================================
# UPDATE BLOOD
# ============================================================

@router.put(
    "/{blood_id}",
    response_model=BloodResponse
)
def update_blood(
    blood_id: int,
    blood: BloodCreate,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    inventory = db.query(BloodInventory).filter(
        BloodInventory.id == blood_id,
        BloodInventory.hospital_id == hospital_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Blood inventory not found"
        )

    if blood.blood_group not in ALLOWED_BLOOD_GROUPS:
        raise HTTPException(
            status_code=400,
            detail="Invalid blood group"
        )

    if blood.units_available < 0:
        raise HTTPException(
            status_code=400,
            detail="Units cannot be negative"
        )

    inventory.blood_group = blood.blood_group
    inventory.units_available = blood.units_available

    db.commit()
    db.refresh(inventory)

    return inventory


# ============================================================
# DELETE BLOOD
# ============================================================

@router.delete("/{blood_id}")
def delete_blood(
    blood_id: int,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    inventory = db.query(BloodInventory).filter(
        BloodInventory.id == blood_id,
        BloodInventory.hospital_id == hospital_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Blood inventory not found"
        )

    db.delete(inventory)
    db.commit()

    return {
        "message": "Blood inventory deleted successfully"
    }