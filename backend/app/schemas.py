from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class GrantBase(BaseModel):
    title: str
    principal_investigator: str
    funding_agency: str
    amount: Decimal
    deadline: date
    status: str = "Pending"
    compliance_status: Optional[str] = None


class GrantCreate(GrantBase):
    pass


class GrantUpdate(BaseModel):
    title: Optional[str] = None
    principal_investigator: Optional[str] = None
    funding_agency: Optional[str] = None
    amount: Optional[Decimal] = None
    deadline: Optional[date] = None
    status: Optional[str] = None
    compliance_status: Optional[str] = None


class GrantResponse(GrantBase):
    id: int

    class Config:
        from_attributes = True
        
class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "Viewer"


class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    file_type: str
    grant_id: int
    uploaded_by: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class AIGrantExtraction(BaseModel):
    title: Optional[str] = None
    principal_investigator: Optional[str] = None
    funding_agency: Optional[str] = None
    amount: Optional[float] = None
    deadline: Optional[date] = None
    status: Optional[str] = None
    compliance_status: Optional[str] = None
    summary: Optional[str] = None