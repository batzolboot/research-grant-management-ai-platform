from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="Viewer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    grant_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    priority = Column(String, nullable=False, default="Medium")
    status = Column(String, nullable=False, default="Open")
    created_by = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(Integer, nullable=True)
    details = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False, unique=True)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    grant_id = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, nullable=False)
    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

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