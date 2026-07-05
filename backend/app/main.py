from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Research Grant Management API",
    description="Backend API for managing research grants, documents, deadlines, dashboards, and AI extraction.",
    version="0.1.0"
)


@app.get("/")
def root():
    return {"message": "Research Grant Management API is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/grants", response_model=schemas.GrantResponse)
def create_grant(grant: schemas.GrantCreate, db: Session = Depends(get_db)):
    return crud.create_grant(db, grant)


@app.get("/grants", response_model=List[schemas.GrantResponse])
def get_grants(db: Session = Depends(get_db)):
    return crud.get_grants(db)


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