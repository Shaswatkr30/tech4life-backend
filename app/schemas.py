from typing import Optional
from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator
)


# ============================================================
# HOSPITAL
# ============================================================

class HospitalCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    address: str = Field(..., min_length=5)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(
        default=None,
        min_length=7,
        max_length=20
    )
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("name", "address", "city", "state")
    @classmethod
    def remove_extra_spaces(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value


class HospitalResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    state: str
    phone: Optional[str]
    email: EmailStr
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        from_attributes = True


class HospitalLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class PublicHospitalResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    state: str
    phone: Optional[str]
    email: EmailStr

    class Config:
        from_attributes = True


# ============================================================
# BLOOD
# ============================================================

class BloodCreate(BaseModel):
    blood_group: str
    units_available: int = Field(..., ge=0)

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value):
        allowed = [
            "A+", "A-",
            "B+", "B-",
            "AB+", "AB-",
            "O+", "O-"
        ]

        value = value.strip().upper()

        if value not in allowed:
            raise ValueError("Invalid blood group")

        return value


class BloodResponse(BaseModel):
    id: int
    hospital_id: int
    blood_group: str
    units_available: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# ICU
# ============================================================

class ICUCreate(BaseModel):
    total_beds: int = Field(..., ge=0)
    available_beds: int = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_beds(self):
        if self.available_beds > self.total_beds:
            raise ValueError(
                "Available beds cannot exceed total beds"
            )

        return self


class ICUResponse(BaseModel):
    id: int
    hospital_id: int
    total_beds: int
    available_beds: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# ORGAN
# ============================================================

class OrganCreate(BaseModel):
    organ_name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )
    available: bool

    @field_validator("organ_name")
    @classmethod
    def validate_organ_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Organ name cannot be empty")

        return value


class OrganResponse(BaseModel):
    id: int
    hospital_id: int
    organ_name: str
    available: bool
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# EQUIPMENT
# ============================================================

class EquipmentCreate(BaseModel):
    equipment_name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )
    total_quantity: int = Field(..., ge=0)
    available_quantity: int = Field(..., ge=0)

    @field_validator("equipment_name")
    @classmethod
    def validate_equipment_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Equipment name cannot be empty"
            )

        return value

    @model_validator(mode="after")
    def validate_quantity(self):
        if self.available_quantity > self.total_quantity:
            raise ValueError(
                "Available quantity cannot exceed total quantity"
            )

        return self


class EquipmentResponse(BaseModel):
    id: int
    hospital_id: int
    equipment_name: str
    total_quantity: int
    available_quantity: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# PUBLIC BLOOD
# ============================================================

class PublicBloodResponse(BaseModel):
    id: int
    hospital_id: int
    hospital_name: str
    city: str
    state: str
    blood_group: str
    units_available: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# PUBLIC ICU
# ============================================================

class PublicICUResponse(BaseModel):
    id: int
    hospital_id: int
    hospital_name: str
    city: str
    state: str
    total_beds: int
    available_beds: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# PUBLIC ORGAN
# ============================================================

class PublicOrganResponse(BaseModel):
    id: int
    hospital_id: int
    hospital_name: str
    city: str
    state: str
    organ_name: str
    available: bool
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# PUBLIC EQUIPMENT
# ============================================================

class PublicEquipmentResponse(BaseModel):
    id: int
    hospital_id: int
    hospital_name: str
    city: str
    state: str
    equipment_name: str
    total_quantity: int
    available_quantity: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# ADMIN
# ============================================================

class AdminLogin(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=100
    )
    password: str = Field(..., min_length=1)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str


class AdminHospitalResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    state: str
    phone: Optional[str]
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True