from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Hospital,
    BloodInventory,
    ICUResource,
    OrganInventory,
    Equipment,
    IntegrationLog,
    Admin,
    ResourceHistory,
    AuditLog
)

from app.schemas import (
    AdminLogin,
    AdminTokenResponse
)

from app.auth import (
    verify_password,
    create_access_token,
    get_current_admin
)


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


# ============================================================
# RESOURCE HISTORY HELPER
# ============================================================

def save_resource_history(
    db,
    hospital_id,
    resource_type,
    resource_id,
    action,
    old_data=None,
    new_data=None
):
    history = ResourceHistory(
        hospital_id=hospital_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        old_data=old_data,
        new_data=new_data
    )

    db.add(history)


# ============================================================
# AUDIT LOG HELPER
# ============================================================

def save_audit_log(
    db,
    admin_id,
    action,
    hospital_id=None,
    resource_type=None,
    resource_id=None,
    details=None
):
    log = AuditLog(
        admin_id=admin_id,
        hospital_id=hospital_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details
    )

    db.add(log)


# ============================================================
# ADMIN LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=AdminTokenResponse
)
def admin_login(
    admin_data: AdminLogin,
    db: Session = Depends(get_db)
):

    admin = db.query(Admin).filter(
        Admin.username == admin_data.username
    ).first()

    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        admin_data.password,
        admin.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=403,
            detail="Admin account is inactive"
        )

    token = create_access_token({
        "admin_id": admin.id,
        "role": "admin"
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ============================================================
# GET ALL HOSPITALS
# ============================================================

@router.get("/hospitals")
def get_all_hospitals(
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    hospitals = db.query(Hospital).order_by(
        Hospital.id.desc()
    ).all()

    return hospitals


# ============================================================
# GET SINGLE HOSPITAL
# ============================================================

@router.get("/hospitals/{hospital_id}")
def get_hospital(
    hospital_id: int,
    admin_id: int = Depends(get_current_admin),
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
# DELETE HOSPITAL
# ============================================================
# ============================================================
# DELETE HOSPITAL
# ============================================================

@router.delete("/hospitals/{hospital_id}")
def delete_hospital(
    hospital_id: int,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # FIND HOSPITAL
    # --------------------------------------------------------

    hospital = db.query(Hospital).filter(
        Hospital.id == hospital_id
    ).first()

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    hospital_name = hospital.name

    try:

        # ----------------------------------------------------
        # SAVE DELETE AUDIT LOG
        # ----------------------------------------------------

        save_audit_log(
            db=db,
            admin_id=admin_id,
            hospital_id=hospital_id,
            action="DELETE",
            resource_type="hospital",
            resource_id=hospital_id,
            details=f"Deleted hospital: {hospital_name}"
        )

        db.flush()

        # ----------------------------------------------------
        # REMOVE HOSPITAL REFERENCE FROM AUDIT LOGS
        #
        # Audit logs are preserved, but hospital_id becomes
        # NULL so PostgreSQL allows the hospital to be deleted.
        # ----------------------------------------------------

        db.query(AuditLog).filter(
            AuditLog.hospital_id == hospital_id
        ).update(
            {
                AuditLog.hospital_id: None
            },
            synchronize_session=False
        )

        # ----------------------------------------------------
        # DELETE RESOURCE HISTORY
        # ----------------------------------------------------

        db.query(ResourceHistory).filter(
            ResourceHistory.hospital_id == hospital_id
        ).delete(
            synchronize_session=False
        )

        # ----------------------------------------------------
        # DELETE INTEGRATION LOGS
        # ----------------------------------------------------

        db.query(IntegrationLog).filter(
            IntegrationLog.hospital_id == hospital_id
        ).delete(
            synchronize_session=False
        )

        # ----------------------------------------------------
        # DELETE BLOOD RECORDS
        # ----------------------------------------------------

        db.query(BloodInventory).filter(
            BloodInventory.hospital_id == hospital_id
        ).delete(
            synchronize_session=False
        )

        # ----------------------------------------------------
        # DELETE ICU RECORDS
        # ----------------------------------------------------

        db.query(ICUResource).filter(
            ICUResource.hospital_id == hospital_id
        ).delete(
            synchronize_session=False
        )

        # ----------------------------------------------------
        # DELETE ORGAN RECORDS
        # ----------------------------------------------------

        db.query(OrganInventory).filter(
            OrganInventory.hospital_id == hospital_id
        ).delete(
            synchronize_session=False
        )

        # ----------------------------------------------------
        # DELETE EQUIPMENT RECORDS
        # ----------------------------------------------------

        db.query(Equipment).filter(
            Equipment.hospital_id == hospital_id
        ).delete(
            synchronize_session=False
        )

        # ----------------------------------------------------
        # DELETE HOSPITAL
        # ----------------------------------------------------

        db.delete(hospital)

        # ----------------------------------------------------
        # COMMIT EVERYTHING
        # ----------------------------------------------------

        db.commit()

        return {
            "message": "Hospital deleted successfully",
            "hospital_id": hospital_id,
            "hospital_name": hospital_name
        }

    except Exception as e:

        # ----------------------------------------------------
        # ROLLBACK IF ANY ERROR OCCURS
        # ----------------------------------------------------

        db.rollback()

        print(
            "Hospital deletion error:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to delete hospital"
        )

   

    hospital = db.query(Hospital).filter(
        Hospital.id == hospital_id
    ).first()

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    hospital_name = hospital.name

    # Audit log BEFORE deleting hospital
    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=hospital_id,
        action="DELETE",
        resource_type="hospital",
        resource_id=hospital_id,
        details=f"Deleted hospital: {hospital_name}"
    )

    # Delete resource history
    db.query(ResourceHistory).filter(
        ResourceHistory.hospital_id == hospital_id
    ).delete(synchronize_session=False)

    # Delete integration logs
    db.query(IntegrationLog).filter(
        IntegrationLog.hospital_id == hospital_id
    ).delete(synchronize_session=False)

    # Delete blood
    db.query(BloodInventory).filter(
        BloodInventory.hospital_id == hospital_id
    ).delete(synchronize_session=False)

    # Delete ICU
    db.query(ICUResource).filter(
        ICUResource.hospital_id == hospital_id
    ).delete(synchronize_session=False)

    # Delete organs
    db.query(OrganInventory).filter(
        OrganInventory.hospital_id == hospital_id
    ).delete(synchronize_session=False)

    # Delete equipment
    db.query(Equipment).filter(
        Equipment.hospital_id == hospital_id
    ).delete(synchronize_session=False)

    # Delete hospital
    db.delete(hospital)

    db.commit()

    return {
        "message": "Hospital deleted successfully"
    }


# ============================================================
# APPROVE / DEACTIVATE HOSPITAL
# ============================================================

@router.put("/hospitals/{hospital_id}/status")
def update_hospital_status(
    hospital_id: int,
    is_active: bool,
    admin_id: int = Depends(get_current_admin),
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

    old_status = hospital.is_active

    hospital.is_active = is_active

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=hospital.id,
        action="STATUS_CHANGE",
        resource_type="hospital",
        resource_id=hospital.id,
        details=(
            f"Hospital status changed "
            f"from {old_status} to {is_active}"
        )
    )

    db.commit()
    db.refresh(hospital)

    return {
        "message": "Hospital status updated successfully",
        "hospital_id": hospital.id,
        "is_active": hospital.is_active
    }


# ============================================================
# ADMIN STATS
# ============================================================

@router.get("/stats")
def admin_stats(
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    total_hospitals = db.query(Hospital).count()

    active_hospitals = db.query(Hospital).filter(
        Hospital.is_active == True
    ).count()

    pending_hospitals = db.query(Hospital).filter(
        Hospital.is_active == False
    ).count()

    total_blood_records = db.query(
        BloodInventory
    ).count()

    total_icu_records = db.query(
        ICUResource
    ).count()

    total_organ_records = db.query(
        OrganInventory
    ).count()

    total_equipment_records = db.query(
        Equipment
    ).count()

    return {
        "total_hospitals": total_hospitals,
        "active_hospitals": active_hospitals,
        "pending_hospitals": pending_hospitals,
        "total_blood_records": total_blood_records,
        "total_icu_records": total_icu_records,
        "total_organ_records": total_organ_records,
        "total_equipment_records": total_equipment_records
    }


# ============================================================
# GET HOSPITAL RESOURCES
# ============================================================

@router.get("/hospitals/{hospital_id}/resources")
def get_hospital_resources(
    hospital_id: int,
    admin_id: int = Depends(get_current_admin),
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

    blood = db.query(BloodInventory).filter(
        BloodInventory.hospital_id == hospital_id
    ).all()

    icu = db.query(ICUResource).filter(
        ICUResource.hospital_id == hospital_id
    ).all()

    organs = db.query(OrganInventory).filter(
        OrganInventory.hospital_id == hospital_id
    ).all()

    equipment = db.query(Equipment).filter(
        Equipment.hospital_id == hospital_id
    ).all()

    return {
        "hospital": {
            "id": hospital.id,
            "name": hospital.name,
            "city": hospital.city,
            "state": hospital.state,
            "email": hospital.email,
            "phone": hospital.phone,
            "is_active": hospital.is_active
        },
        "blood": blood,
        "icu": icu,
        "organs": organs,
        "equipment": equipment
    }


# ============================================================
# ADD BLOOD
# ============================================================

@router.post("/hospitals/{hospital_id}/blood")
def add_blood_record(
    hospital_id: int,
    blood_group: str,
    units_available: int,
    admin_id: int = Depends(get_current_admin),
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

    if units_available < 0:
        raise HTTPException(
            status_code=400,
            detail="Units cannot be negative"
        )

    blood = BloodInventory(
        hospital_id=hospital_id,
        blood_group=blood_group,
        units_available=units_available
    )

    db.add(blood)
    db.commit()
    db.refresh(blood)

    save_resource_history(
        db=db,
        hospital_id=hospital_id,
        resource_type="blood",
        resource_id=blood.id,
        action="add",
        old_data=None,
        new_data=(
            f"Blood Group: {blood.blood_group}, "
            f"Units: {blood.units_available}"
        )
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=hospital_id,
        action="ADD",
        resource_type="blood",
        resource_id=blood.id,
        details=(
            f"Added blood group {blood.blood_group} "
            f"with {blood.units_available} units"
        )
    )

    db.commit()

    return {
        "message": "Blood record added successfully",
        "id": blood.id
    }


# ============================================================
# UPDATE BLOOD
# ============================================================

@router.put("/blood/{blood_id}")
def update_blood_record(
    blood_id: int,
    blood_group: str,
    units_available: int,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    blood = db.query(BloodInventory).filter(
        BloodInventory.id == blood_id
    ).first()

    if not blood:
        raise HTTPException(
            status_code=404,
            detail="Blood record not found"
        )

    if units_available < 0:
        raise HTTPException(
            status_code=400,
            detail="Units cannot be negative"
        )

    old_data = (
        f"Blood Group: {blood.blood_group}, "
        f"Units: {blood.units_available}"
    )

    blood.blood_group = blood_group
    blood.units_available = units_available

    new_data = (
        f"Blood Group: {blood.blood_group}, "
        f"Units: {blood.units_available}"
    )

    save_resource_history(
        db=db,
        hospital_id=blood.hospital_id,
        resource_type="blood",
        resource_id=blood.id,
        action="update",
        old_data=old_data,
        new_data=new_data
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=blood.hospital_id,
        action="UPDATE",
        resource_type="blood",
        resource_id=blood.id,
        details=(
            f"Changed blood record from "
            f"[{old_data}] to [{new_data}]"
        )
    )

    db.commit()
    db.refresh(blood)

    return {
        "message": "Blood record updated successfully"
    }


# ============================================================
# DELETE BLOOD
# ============================================================

@router.delete("/blood/{blood_id}")
def delete_blood_record(
    blood_id: int,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    blood = db.query(BloodInventory).filter(
        BloodInventory.id == blood_id
    ).first()

    if not blood:
        raise HTTPException(
            status_code=404,
            detail="Blood record not found"
        )

    old_data = (
        f"Blood Group: {blood.blood_group}, "
        f"Units: {blood.units_available}"
    )

    save_resource_history(
        db=db,
        hospital_id=blood.hospital_id,
        resource_type="blood",
        resource_id=blood.id,
        action="delete",
        old_data=old_data,
        new_data=None
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=blood.hospital_id,
        action="DELETE",
        resource_type="blood",
        resource_id=blood.id,
        details=f"Deleted blood record: {old_data}"
    )

    db.delete(blood)
    db.commit()

    return {
        "message": "Blood record deleted successfully"
    }


# ============================================================
# ADD ICU
# ============================================================

@router.post("/hospitals/{hospital_id}/icu")
def add_icu_record(
    hospital_id: int,
    total_beds: int,
    available_beds: int,
    admin_id: int = Depends(get_current_admin),
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

    if total_beds < 0 or available_beds < 0:
        raise HTTPException(
            status_code=400,
            detail="Bed values cannot be negative"
        )

    if available_beds > total_beds:
        raise HTTPException(
            status_code=400,
            detail="Available beds cannot exceed total beds"
        )

    icu = ICUResource(
        hospital_id=hospital_id,
        total_beds=total_beds,
        available_beds=available_beds
    )

    db.add(icu)
    db.commit()
    db.refresh(icu)

    save_resource_history(
        db=db,
        hospital_id=hospital_id,
        resource_type="icu",
        resource_id=icu.id,
        action="add",
        old_data=None,
        new_data=(
            f"Total Beds: {icu.total_beds}, "
            f"Available Beds: {icu.available_beds}"
        )
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=hospital_id,
        action="ADD",
        resource_type="icu",
        resource_id=icu.id,
        details=(
            f"Added ICU record: "
            f"Total Beds={icu.total_beds}, "
            f"Available Beds={icu.available_beds}"
        )
    )

    db.commit()

    return {
        "message": "ICU record added successfully",
        "id": icu.id
    }


# ============================================================
# UPDATE ICU
# ============================================================

@router.put("/icu/{icu_id}")
def update_icu_record(
    icu_id: int,
    total_beds: int,
    available_beds: int,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    icu = db.query(ICUResource).filter(
        ICUResource.id == icu_id
    ).first()

    if not icu:
        raise HTTPException(
            status_code=404,
            detail="ICU record not found"
        )

    if total_beds < 0 or available_beds < 0:
        raise HTTPException(
            status_code=400,
            detail="Bed values cannot be negative"
        )

    if available_beds > total_beds:
        raise HTTPException(
            status_code=400,
            detail="Available beds cannot exceed total beds"
        )

    old_data = (
        f"Total Beds: {icu.total_beds}, "
        f"Available Beds: {icu.available_beds}"
    )

    icu.total_beds = total_beds
    icu.available_beds = available_beds

    new_data = (
        f"Total Beds: {icu.total_beds}, "
        f"Available Beds: {icu.available_beds}"
    )

    save_resource_history(
        db=db,
        hospital_id=icu.hospital_id,
        resource_type="icu",
        resource_id=icu.id,
        action="update",
        old_data=old_data,
        new_data=new_data
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=icu.hospital_id,
        action="UPDATE",
        resource_type="icu",
        resource_id=icu.id,
        details=(
            f"Changed ICU record from "
            f"[{old_data}] to [{new_data}]"
        )
    )

    db.commit()
    db.refresh(icu)

    return {
        "message": "ICU record updated successfully"
    }


# ============================================================
# DELETE ICU
# ============================================================

@router.delete("/icu/{icu_id}")
def delete_icu_record(
    icu_id: int,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    icu = db.query(ICUResource).filter(
        ICUResource.id == icu_id
    ).first()

    if not icu:
        raise HTTPException(
            status_code=404,
            detail="ICU record not found"
        )

    old_data = (
        f"Total Beds: {icu.total_beds}, "
        f"Available Beds: {icu.available_beds}"
    )

    save_resource_history(
        db=db,
        hospital_id=icu.hospital_id,
        resource_type="icu",
        resource_id=icu.id,
        action="delete",
        old_data=old_data,
        new_data=None
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=icu.hospital_id,
        action="DELETE",
        resource_type="icu",
        resource_id=icu.id,
        details=f"Deleted ICU record: {old_data}"
    )

    db.delete(icu)
    db.commit()

    return {
        "message": "ICU record deleted successfully"
    }


# ============================================================
# ADD ORGAN
# ============================================================

@router.post("/hospitals/{hospital_id}/organs")
def add_organ_record(
    hospital_id: int,
    organ_name: str,
    available: bool,
    admin_id: int = Depends(get_current_admin),
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

    organ = OrganInventory(
        hospital_id=hospital_id,
        organ_name=organ_name,
        available=available
    )

    db.add(organ)
    db.commit()
    db.refresh(organ)

    save_resource_history(
        db=db,
        hospital_id=hospital_id,
        resource_type="organ",
        resource_id=organ.id,
        action="add",
        old_data=None,
        new_data=(
            f"Organ: {organ.organ_name}, "
            f"Available: {organ.available}"
        )
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=hospital_id,
        action="ADD",
        resource_type="organ",
        resource_id=organ.id,
        details=(
            f"Added organ: {organ.organ_name}, "
            f"Available={organ.available}"
        )
    )

    db.commit()

    return {
        "message": "Organ record added successfully",
        "id": organ.id
    }


# ============================================================
# UPDATE ORGAN
# ============================================================

@router.put("/organs/{organ_id}")
def update_organ_record(
    organ_id: int,
    organ_name: str,
    available: bool,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    organ = db.query(OrganInventory).filter(
        OrganInventory.id == organ_id
    ).first()

    if not organ:
        raise HTTPException(
            status_code=404,
            detail="Organ record not found"
        )

    old_data = (
        f"Organ: {organ.organ_name}, "
        f"Available: {organ.available}"
    )

    organ.organ_name = organ_name
    organ.available = available

    new_data = (
        f"Organ: {organ.organ_name}, "
        f"Available: {organ.available}"
    )

    save_resource_history(
        db=db,
        hospital_id=organ.hospital_id,
        resource_type="organ",
        resource_id=organ.id,
        action="update",
        old_data=old_data,
        new_data=new_data
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=organ.hospital_id,
        action="UPDATE",
        resource_type="organ",
        resource_id=organ.id,
        details=(
            f"Changed organ from "
            f"[{old_data}] to [{new_data}]"
        )
    )

    db.commit()
    db.refresh(organ)

    return {
        "message": "Organ record updated successfully"
    }


# ============================================================
# DELETE ORGAN
# ============================================================

@router.delete("/organs/{organ_id}")
def delete_organ_record(
    organ_id: int,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    organ = db.query(OrganInventory).filter(
        OrganInventory.id == organ_id
    ).first()

    if not organ:
        raise HTTPException(
            status_code=404,
            detail="Organ record not found"
        )

    old_data = (
        f"Organ: {organ.organ_name}, "
        f"Available: {organ.available}"
    )

    save_resource_history(
        db=db,
        hospital_id=organ.hospital_id,
        resource_type="organ",
        resource_id=organ.id,
        action="delete",
        old_data=old_data,
        new_data=None
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=organ.hospital_id,
        action="DELETE",
        resource_type="organ",
        resource_id=organ.id,
        details=f"Deleted organ record: {old_data}"
    )

    db.delete(organ)
    db.commit()

    return {
        "message": "Organ record deleted successfully"
    }


# ============================================================
# ADD EQUIPMENT
# ============================================================

@router.post("/hospitals/{hospital_id}/equipment")
def add_equipment_record(
    hospital_id: int,
    equipment_name: str,
    total_quantity: int,
    available_quantity: int,
    admin_id: int = Depends(get_current_admin),
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

    if total_quantity < 0 or available_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative"
        )

    if available_quantity > total_quantity:
        raise HTTPException(
            status_code=400,
            detail="Available quantity cannot exceed total quantity"
        )

    equipment = Equipment(
        hospital_id=hospital_id,
        equipment_name=equipment_name,
        total_quantity=total_quantity,
        available_quantity=available_quantity
    )

    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    save_resource_history(
        db=db,
        hospital_id=hospital_id,
        resource_type="equipment",
        resource_id=equipment.id,
        action="add",
        old_data=None,
        new_data=(
            f"Equipment: {equipment.equipment_name}, "
            f"Total: {equipment.total_quantity}, "
            f"Available: {equipment.available_quantity}"
        )
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=hospital_id,
        action="ADD",
        resource_type="equipment",
        resource_id=equipment.id,
        details=(
            f"Added equipment: {equipment.equipment_name}, "
            f"Total={equipment.total_quantity}, "
            f"Available={equipment.available_quantity}"
        )
    )

    db.commit()

    return {
        "message": "Equipment record added successfully",
        "id": equipment.id
    }


# ============================================================
# UPDATE EQUIPMENT
# ============================================================

@router.put("/equipment/{equipment_id}")
def update_equipment_record(
    equipment_id: int,
    equipment_name: str,
    total_quantity: int,
    available_quantity: int,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    equipment = db.query(Equipment).filter(
        Equipment.id == equipment_id
    ).first()

    if not equipment:
        raise HTTPException(
            status_code=404,
            detail="Equipment record not found"
        )

    if total_quantity < 0 or available_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative"
        )

    if available_quantity > total_quantity:
        raise HTTPException(
            status_code=400,
            detail="Available quantity cannot exceed total quantity"
        )

    old_data = (
        f"Equipment: {equipment.equipment_name}, "
        f"Total: {equipment.total_quantity}, "
        f"Available: {equipment.available_quantity}"
    )

    equipment.equipment_name = equipment_name
    equipment.total_quantity = total_quantity
    equipment.available_quantity = available_quantity

    new_data = (
        f"Equipment: {equipment.equipment_name}, "
        f"Total: {equipment.total_quantity}, "
        f"Available: {equipment.available_quantity}"
    )

    save_resource_history(
        db=db,
        hospital_id=equipment.hospital_id,
        resource_type="equipment",
        resource_id=equipment.id,
        action="update",
        old_data=old_data,
        new_data=new_data
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=equipment.hospital_id,
        action="UPDATE",
        resource_type="equipment",
        resource_id=equipment.id,
        details=(
            f"Changed equipment from "
            f"[{old_data}] to [{new_data}]"
        )
    )

    db.commit()
    db.refresh(equipment)

    return {
        "message": "Equipment record updated successfully"
    }


# ============================================================
# DELETE EQUIPMENT
# ============================================================

@router.delete("/equipment/{equipment_id}")
def delete_equipment_record(
    equipment_id: int,
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    equipment = db.query(Equipment).filter(
        Equipment.id == equipment_id
    ).first()

    if not equipment:
        raise HTTPException(
            status_code=404,
            detail="Equipment record not found"
        )

    old_data = (
        f"Equipment: {equipment.equipment_name}, "
        f"Total: {equipment.total_quantity}, "
        f"Available: {equipment.available_quantity}"
    )

    save_resource_history(
        db=db,
        hospital_id=equipment.hospital_id,
        resource_type="equipment",
        resource_id=equipment.id,
        action="delete",
        old_data=old_data,
        new_data=None
    )

    save_audit_log(
        db=db,
        admin_id=admin_id,
        hospital_id=equipment.hospital_id,
        action="DELETE",
        resource_type="equipment",
        resource_id=equipment.id,
        details=f"Deleted equipment record: {old_data}"
    )

    db.delete(equipment)
    db.commit()

    return {
        "message": "Equipment record deleted successfully"
    }


# ============================================================
# RESOURCE HISTORY
# ============================================================

@router.get("/hospitals/{hospital_id}/history")
def get_resource_history(
    hospital_id: int,
    admin_id: int = Depends(get_current_admin),
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

    history = db.query(ResourceHistory).filter(
        ResourceHistory.hospital_id == hospital_id
    ).order_by(
        ResourceHistory.id.desc()
    ).all()

    return history


# ============================================================
# ALL AUDIT LOGS
# ============================================================

@router.get("/audit-logs")
def get_audit_logs(
    admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):

    logs = db.query(AuditLog).order_by(
        AuditLog.id.desc()
    ).all()

    return logs


# ============================================================
# HOSPITAL AUDIT LOGS
# ============================================================

@router.get("/hospitals/{hospital_id}/audit-logs")
def get_hospital_audit_logs(
    hospital_id: int,
    admin_id: int = Depends(get_current_admin),
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

    logs = db.query(AuditLog).filter(
        AuditLog.hospital_id == hospital_id
    ).order_by(
        AuditLog.id.desc()
    ).all()

    return logs