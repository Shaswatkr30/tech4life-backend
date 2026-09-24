from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OrganInventory, Hospital

from app.schemas import (
    OrganCreate,
    OrganResponse,
    PublicOrganResponse
)

from app.auth import get_current_hospital


router = APIRouter(
    prefix="/api/organs",
    tags=["Organ Inventory"]
)


# ============================================================
# ADD ORGAN
# ============================================================

@router.post(
    "/",
    response_model=OrganResponse
)
def add_organ(
    organ: OrganCreate,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    organ_name = organ.organ_name.strip()

    if not organ_name:
        raise HTTPException(
            status_code=400,
            detail="Organ name is required"
        )

    existing = db.query(OrganInventory).filter(
        OrganInventory.hospital_id == hospital_id,
        OrganInventory.organ_name == organ_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This organ already exists"
        )

    new_organ = OrganInventory(
        hospital_id=hospital_id,
        organ_name=organ_name,
        available=organ.available
    )

    db.add(new_organ)
    db.commit()
    db.refresh(new_organ)

    return new_organ


# ============================================================
# GET MY ORGANS
# ============================================================

@router.get(
    "/my",
    response_model=list[OrganResponse]
)
def get_my_organs(
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    return db.query(OrganInventory).filter(
        OrganInventory.hospital_id == hospital_id
    ).all()


# ============================================================
# PUBLIC ORGANS
# ============================================================

@router.get(
    "/public",
    response_model=list[PublicOrganResponse]
)
def get_public_organs(
    db: Session = Depends(get_db)
):

    results = db.query(
        OrganInventory,
        Hospital
    ).join(
        Hospital,
        OrganInventory.hospital_id == Hospital.id
    ).all()

    return [
        {
            "id": organ.id,
            "hospital_id": hospital.id,
            "hospital_name": hospital.name,
            "city": hospital.city,
            "state": hospital.state,
            "organ_name": organ.organ_name,
            "available": organ.available,
            "updated_at": organ.updated_at
        }

        for organ, hospital in results
    ]


# ============================================================
# UPDATE ORGAN
# ============================================================

@router.put(
    "/{organ_id}",
    response_model=OrganResponse
)
def update_organ(
    organ_id: int,
    organ: OrganCreate,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    resource = db.query(OrganInventory).filter(
        OrganInventory.id == organ_id,
        OrganInventory.hospital_id == hospital_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Organ not found"
        )

    organ_name = organ.organ_name.strip()

    if not organ_name:
        raise HTTPException(
            status_code=400,
            detail="Organ name is required"
        )

    resource.organ_name = organ_name
    resource.available = organ.available

    db.commit()
    db.refresh(resource)

    return resource


# ============================================================
# DELETE ORGAN
# ============================================================

@router.delete("/{organ_id}")
def delete_organ(
    organ_id: int,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    resource = db.query(OrganInventory).filter(
        OrganInventory.id == organ_id,
        OrganInventory.hospital_id == hospital_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Organ not found"
        )

    db.delete(resource)
    db.commit()

    return {
        "message": "Organ deleted successfully"
    }