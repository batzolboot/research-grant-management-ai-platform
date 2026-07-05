from typing import Optional
from pydantic import BaseModel


class GrantBase(BaseModel):
    title: str
    principal_investigator: str
    funding_agency: str
    amount: float
    deadline: str
    status: str = "Pending"
    compliance_status: Optional[str] = None


class GrantCreate(GrantBase):
    pass


class GrantUpdate(BaseModel):
    title: Optional[str] = None
    principal_investigator: Optional[str] = None
    funding_agency: Optional[str] = None
    amount: Optional[float] = None
    deadline: Optional[str] = None
    status: Optional[str] = None
    compliance_status: Optional[str] = None


class GrantResponse(GrantBase):
    id: int

    class Config:
        from_attributes = True