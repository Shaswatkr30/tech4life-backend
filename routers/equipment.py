from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Equipment, Hospital

from app.schemas import (
    EquipmentCreate,
    EquipmentResponse,
    PublicEquipmentResponse
)

from app.auth import get_current_hospital


router = APIRouter(
    prefix="/api/equipment",
    tags=["Medical Equipment"]
)


# ============================================================
# ADD EQUIPMENT
# ============================================================

@router.post(
    "/",
    response_model=EquipmentResponse
)
def add_equipment(
    equipment: EquipmentCreate,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    if equipment.total_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Total quantity cannot be negative"
        )

    if equipment.available_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Available quantity cannot be negative"
        )

    if equipment.available_quantity > equipment.total_quantity:
        raise HTTPException(
            status_code=400,
            detail="Available quantity cannot exceed total quantity"
        )

    name = equipment.equipment_name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Equipment name is required"
        )

    existing = db.query(Equipment).filter(
        Equipment.hospital_id == hospital_id,
        Equipment.equipment_name == name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This equipment already exists"
        )

    new_equipment = Equipment(
        hospital_id=hospital_id,
        equipment_name=name,
        total_quantity=equipment.total_quantity,
        available_quantity=equipment.available_quantity
    )

    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)

    return new_equipment


# ============================================================
# GET MY EQUIPMENT
# ============================================================

@router.get(
    "/my",
    response_model=list[EquipmentResponse]
)
def get_my_equipment(
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    return db.query(Equipment).filter(
        Equipment.hospital_id == hospital_id
    ).all()


# ============================================================
# PUBLIC EQUIPMENT
# ============================================================

@router.get(
    "/public",
    response_model=list[PublicEquipmentResponse]
)
def get_public_equipment(
    db: Session = Depends(get_db)
):

    results = db.query(
        Equipment,
        Hospital
    ).join(
        Hospital,
        Equipment.hospital_id == Hospital.id
    ).all()

    return [
        {
            "id": equipment.id,
            "hospital_id": hospital.id,
            "hospital_name": hospital.name,
            "city": hospital.city,
            "state": hospital.state,
            "equipment_name": equipment.equipment_name,
            "total_quantity": equipment.total_quantity,
            "available_quantity": equipment.available_quantity,
            "updated_at": equipment.updated_at
        }

        for equipment, hospital in results
    ]


# ============================================================
# UPDATE EQUIPMENT
# ============================================================

@router.put(
    "/{equipment_id}",
    response_model=EquipmentResponse
)
def update_equipment(
    equipment_id: int,
    equipment: EquipmentCreate,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    resource = db.query(Equipment).filter(
        Equipment.id == equipment_id,
        Equipment.hospital_id == hospital_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Equipment not found"
        )

    if equipment.total_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Total quantity cannot be negative"
        )

    if equipment.available_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Available quantity cannot be negative"
        )

    if equipment.available_quantity > equipment.total_quantity:
        raise HTTPException(
            status_code=400,
            detail="Available quantity cannot exceed total quantity"
        )

    name = equipment.equipment_name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Equipment name is required"
        )

    resource.equipment_name = name
    resource.total_quantity = equipment.total_quantity
    resource.available_quantity = equipment.available_quantity

    db.commit()
    db.refresh(resource)

    return resource


# ============================================================
# DELETE EQUIPMENT
# ============================================================

@router.delete("/{equipment_id}")
def delete_equipment(
    equipment_id: int,
    hospital_id: int = Depends(get_current_hospital),
    db: Session = Depends(get_db)
):

    resource = db.query(Equipment).filter(
        Equipment.id == equipment_id,
        Equipment.hospital_id == hospital_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Equipment not found"
        )

    db.delete(resource)
    db.commit()

    return {
        "message": "Equipment deleted successfully"
    }