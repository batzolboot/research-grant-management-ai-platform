from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal
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

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: int
    grant_id: int
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    created_by: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    status: Optional[Literal["Open", "Completed"]] = None
    priority: Optional[Literal["Low", "Medium", "High"]] = None