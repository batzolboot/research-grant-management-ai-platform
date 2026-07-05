from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from sqlalchemy import func
from app import models, schemas, crud
from app.database import engine, get_db
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Research Grant Management API",
    description="Backend API for managing research grants, documents, deadlines, dashboards, and AI extraction.",
    version="0.1.0"
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


@app.post("/grants", response_model=schemas.GrantResponse, status_code=status.HTTP_201_CREATED)
def create_grant(grant: schemas.GrantCreate, db: Session = Depends(get_db)):
    return crud.create_grant(db, grant)


@app.get("/grants", response_model=List[schemas.GrantResponse])
def get_grants(
    principal_investigator: str | None = None,
    funding_agency: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    return crud.get_grants(
        db,
        principal_investigator=principal_investigator,
        funding_agency=funding_agency,
        status=status
    )


@app.get("/grants/{grant_id}", response_model=schemas.GrantResponse)
def get_grant(grant_id: int, db: Session = Depends(get_db)):
    grant = crud.get_grant(db, grant_id)

    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    return grant


@app.put("/grants/{grant_id}", response_model=schemas.GrantResponse)
def update_grant(
    grant_id: int,
    grant_update: schemas.GrantUpdate,
    db: Session = Depends(get_db)
):
    grant = crud.update_grant(db, grant_id, grant_update)

    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    return grant


@app.delete("/grants/{grant_id}")
def delete_grant(grant_id: int, db: Session = Depends(get_db)):
    grant = crud.delete_grant(db, grant_id)

    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    return {"message": "Grant deleted successfully"}

@app.get("/dashboard/charts")
def dashboard_charts(db: Session = Depends(get_db)):
    grants_by_status = (
        db.query(models.Grant.status, func.count(models.Grant.id))
        .group_by(models.Grant.status)
        .all()
    )

    funding_by_agency = (
        db.query(models.Grant.funding_agency, func.sum(models.Grant.amount))
        .group_by(models.Grant.funding_agency)
        .all()
    )

    return {
        "grants_by_status": [
            {"status": status, "count": count}
            for status, count in grants_by_status
        ],
        "funding_by_agency": [
            {"agency": agency, "funding": float(funding)}
            for agency, funding in funding_by_agency
        ],
    }