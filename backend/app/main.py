from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import auth, crud, models, schemas
from app.database import engine, get_db


models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Research Grant Management API",
    description=(
        "Backend API for managing research grants, documents, "
        "deadlines, dashboards, and AI extraction."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Research Grant Management API is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post(
    "/auth/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = crud.get_user_by_email(db, user.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = auth.hash_password(user.password)

    return crud.create_user(
        db=db,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
    )


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login_user(
    user: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    db_user = crud.get_user_by_email(db, user.email)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = auth.create_access_token(
        data={
            "sub": db_user.email,
            "role": db_user.role,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@app.post(
    "/grants",
    response_model=schemas.GrantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_grant(
    grant: schemas.GrantCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth.require_admin),
):
    return crud.create_grant(db, grant)


@app.get("/grants", response_model=List[schemas.GrantResponse])
def get_grants(
    principal_investigator: str | None = None,
    funding_agency: str | None = None,
    grant_status: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    return crud.get_grants(
        db,
        principal_investigator=principal_investigator,
        funding_agency=funding_agency,
        status=grant_status,
    )


@app.get("/grants/{grant_id}", response_model=schemas.GrantResponse)
def get_grant(
    grant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    grant = crud.get_grant(db, grant_id)

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found",
        )

    return grant


@app.put("/grants/{grant_id}", response_model=schemas.GrantResponse)
def update_grant(
    grant_id: int,
    grant_update: schemas.GrantUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(auth.require_admin),
):
    grant = crud.update_grant(db, grant_id, grant_update)

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found",
        )

    return grant


@app.delete("/grants/{grant_id}")
def delete_grant(
    grant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.require_admin),
):
    grant = crud.delete_grant(db, grant_id)

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found",
        )

    return {"message": "Grant deleted successfully"}


@app.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    total_grants = db.query(models.Grant).count()

    total_funding = (
        db.query(func.sum(models.Grant.amount)).scalar() or 0
    )

    active_grants = (
        db.query(models.Grant)
        .filter(models.Grant.status.ilike("Active"))
        .count()
    )

    missing_compliance = (
        db.query(models.Grant)
        .filter(models.Grant.compliance_status.is_(None))
        .count()
    )

    return {
        "total_grants": total_grants,
        "total_funding": float(total_funding),
        "active_grants": active_grants,
        "missing_compliance": missing_compliance,
    }


@app.get("/dashboard/charts")
def dashboard_charts(
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    grants_by_status = (
        db.query(
            models.Grant.status,
            func.count(models.Grant.id),
        )
        .group_by(models.Grant.status)
        .all()
    )

    funding_by_agency = (
        db.query(
            models.Grant.funding_agency,
            func.sum(models.Grant.amount),
        )
        .group_by(models.Grant.funding_agency)
        .all()
    )

    return {
        "grants_by_status": [
            {
                "status": grant_status,
                "count": count,
            }
            for grant_status, count in grants_by_status
        ],
        "funding_by_agency": [
            {
                "agency": agency,
                "funding": float(funding),
            }
            for agency, funding in funding_by_agency
        ],
    }