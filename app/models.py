from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text
)

from sqlalchemy.sql import func

from .database import Base


# ============================================================
# HOSPITAL
# ============================================================

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)

    address = Column(Text, nullable=False)

    city = Column(String(100), nullable=False)

    state = Column(String(100), nullable=False)

    phone = Column(String(20))

    email = Column(String(150), unique=True, nullable=False)

    latitude = Column(Float)

    longitude = Column(Float)

    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ============================================================
# BLOOD INVENTORY
# ============================================================

class BloodInventory(Base):
    __tablename__ = "blood_inventory"

    id = Column(Integer, primary_key=True, index=True)

    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=False
    )

    blood_group = Column(
        String(10),
        nullable=False
    )

    units_available = Column(
        Integer,
        default=0,
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


# ============================================================
# ORGAN INVENTORY
# ============================================================

class OrganInventory(Base):
    __tablename__ = "organ_inventory"

    id = Column(Integer, primary_key=True, index=True)

    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=False
    )

    organ_name = Column(
        String(100),
        nullable=False
    )

    available = Column(
        Boolean,
        default=False,
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


# ============================================================
# ICU RESOURCE
# ============================================================

class ICUResource(Base):
    __tablename__ = "icu_resources"

    id = Column(Integer, primary_key=True, index=True)

    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=False
    )

    total_beds = Column(
        Integer,
        default=0,
        nullable=False
    )

    available_beds = Column(
        Integer,
        default=0,
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


# ============================================================
# MEDICAL EQUIPMENT
# ============================================================

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)

    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=False
    )

    equipment_name = Column(
        String(150),
        nullable=False
    )

    total_quantity = Column(
        Integer,
        default=0,
        nullable=False
    )

    available_quantity = Column(
        Integer,
        default=0,
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


# ============================================================
# INTEGRATION LOG
# ============================================================

class IntegrationLog(Base):
    __tablename__ = "integration_logs"

    id = Column(Integer, primary_key=True, index=True)

    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=False
    )

    source = Column(String(100))

    status = Column(String(50))

    message = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ============================================================
# ADMIN
# ============================================================

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(100),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # ============================================================
# RESOURCE HISTORY
# ============================================================

class ResourceHistory(Base):
    __tablename__ = "resource_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=False
    )

    resource_type = Column(
        String(50),
        nullable=False
    )

    resource_id = Column(
        Integer,
        nullable=False
    )

    action = Column(
        String(50),
        nullable=False
    )

    old_data = Column(
        Text
    )

    new_data = Column(
        Text
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    admin_id = Column(
        Integer,
        ForeignKey("admins.id"),
        nullable=True
    )

    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=True
    )

    action = Column(
        String(100),
        nullable=False
    )

    resource_type = Column(
        String(50),
        nullable=True
    )

    resource_id = Column(
        Integer,
        nullable=True
    )

    details = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )