from sqlalchemy.orm import Session
from app import models, schemas


def create_grant(db: Session, grant: schemas.GrantCreate):
    db_grant = models.Grant(**grant.model_dump())
    db.add(db_grant)
    db.commit()
    db.refresh(db_grant)
    return db_grant


def get_grants(
    db: Session,
    principal_investigator: str | None = None,
    funding_agency: str | None = None,
    status: str | None = None,
):
    query = db.query(models.Grant)

    if principal_investigator:
        query = query.filter(
            models.Grant.principal_investigator.ilike(f"%{principal_investigator}%")
        )

    if funding_agency:
        query = query.filter(
            models.Grant.funding_agency.ilike(f"%{funding_agency}%")
        )

    if status:
        query = query.filter(
            models.Grant.status.ilike(f"%{status}%")
        )

    return query.all()


def get_grant(db: Session, grant_id: int):
    return db.query(models.Grant).filter(models.Grant.id == grant_id).first()


def update_grant(db: Session, grant_id: int, grant_update: schemas.GrantUpdate):
    db_grant = get_grant(db, grant_id)

    if not db_grant:
        return None

    update_data = grant_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_grant, key, value)

    db.commit()
    db.refresh(db_grant)
    return db_grant


def delete_grant(db: Session, grant_id: int):
    db_grant = get_grant(db, grant_id)

    if not db_grant:
        return None

    db.delete(db_grant)
    db.commit()
    return db_grant

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, email: str, hashed_password: str, role: str):
    user = models.User(
        email=email,
        hashed_password=hashed_password,
        role=role
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def create_document(
    db: Session,
    original_filename: str,
    stored_filename: str,
    file_type: str,
    file_path: str,
    grant_id: int,
    uploaded_by: int,
):
    document = models.Document(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        file_path=file_path,
        grant_id=grant_id,
        uploaded_by=uploaded_by,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_documents(db: Session):
    return (
        db.query(models.Document)
        .order_by(models.Document.uploaded_at.desc())
        .all()
    )