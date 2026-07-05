from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric
from sqlalchemy.sql import func
from app.database import Base


class Grant(Base):
    __tablename__ = "grants"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    principal_investigator = Column(String, nullable=False)
    funding_agency = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    deadline = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="Pending")
    compliance_status = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())