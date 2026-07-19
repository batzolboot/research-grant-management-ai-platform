from pathlib import Path
from typing import List
from uuid import uuid4

import csv
import os

from io import BytesIO, StringIO

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse

import pandas as pd
from pypdf import PdfReader

from openai import OpenAI

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import auth, crud, models, schemas
from app.database import engine, get_db


models.Base.metadata.create_all(bind=engine)

UPLOAD_DIRECTORY = Path("uploads")
UPLOAD_DIRECTORY.mkdir(exist_ok=True)

ALLOWED_FILE_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE = 10 * 1024 * 1024
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")

def extract_document_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        reader = PdfReader(str(file_path))

        pages = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                pages.append(page_text)

        return "\n\n".join(pages)

    if extension == ".csv":
        rows = []

        with file_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.reader(csv_file)

            for row in reader:
                rows.append(" | ".join(row))

        return "\n".join(rows)

    if extension in {".xlsx", ".xls"}:
        spreadsheet = pd.read_excel(file_path)

        return spreadsheet.to_csv(
            index=False,
            sep=" | ",
        )

    raise ValueError("Unsupported file type")


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
        "https://research-grant-management-ai-platfo.vercel.app/",
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
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    db_user = crud.get_user_by_email(db, form_data.username)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not auth.verify_password(
        form_data.password,
        db_user.hashed_password,
    ):
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

@app.get("/auth/me", response_model=schemas.UserResponse)
def get_logged_in_user(
    current_user=Depends(auth.get_current_user),
):
    return current_user

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
    created_grant = crud.create_grant(db, grant)

    crud.create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        resource_type="Grant",
        resource_id=created_grant.id,
        details=f"Created grant: {created_grant.title}",
    )

    if not created_grant.compliance_status:
        crud.create_task(
            db=db,
            grant_id=created_grant.id,
            title="Review missing compliance",
            description=(
                f"Grant '{created_grant.title}' has no compliance status."
            ),
            priority="High",
            created_by=current_user.id,
        )

    return created_grant


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

    crud.create_audit_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        resource_type="Grant",
        resource_id=grant.id,
        details=f"Updated grant: {grant.title}",
    )

    return grant


@app.delete("/grants/{grant_id}")
def delete_grant(
    grant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.require_admin),
):
    grant = crud.get_grant(db, grant_id)

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found",
        )

    grant_title = grant.title

    crud.delete_grant(db, grant_id)

    crud.create_audit_log(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        resource_type="Grant",
        resource_id=grant_id,
        details=f"Deleted grant: {grant_title}",
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

@app.post(
    "/documents/upload",
    response_model=schemas.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    grant_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(auth.require_admin),
):
    grant = crud.get_grant(db, grant_id)

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found",
        )

    original_filename = file.filename or "uploaded_file"
    file_extension = Path(original_filename).suffix.lower()

    if file_extension not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, CSV, XLS, and XLSX files are allowed",
        )

    file_contents = await file.read()

    if len(file_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File must be 10 MB or smaller",
        )

    stored_filename = f"{uuid4()}{file_extension}"
    file_path = UPLOAD_DIRECTORY / stored_filename

    try:
        file_path.write_bytes(file_contents)
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save uploaded file",
        )

    return crud.create_document(
        db=db,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file.content_type or "application/octet-stream",
        file_path=str(file_path),
        grant_id=grant_id,
        uploaded_by=current_user.id,
    )

@app.get(
    "/documents",
    response_model=List[schemas.DocumentResponse],
)
def list_documents(
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    return crud.get_documents(db)

@app.get("/documents/{document_id}/file")
def get_document_file(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    document = (
        db.query(models.Document)
        .filter(models.Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    file_path = Path(document.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file not found",
        )

    return FileResponse(
        path=file_path,
        filename=document.original_filename,
        media_type=document.file_type,
    )

@app.get("/documents/{document_id}/extract")
def extract_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    uploaded_document = (
        db.query(models.Document)
        .filter(models.Document.id == document_id)
        .first()
    )

    if not uploaded_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    file_path = Path(uploaded_document.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file not found",
        )

    try:
        extracted_text = extract_document_text(file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not extract text from document",
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text was found",
        )

    return {
        "document_id": uploaded_document.id,
        "filename": uploaded_document.original_filename,
        "character_count": len(extracted_text),
        "text": extracted_text,
    }

@app.post(
    "/documents/{document_id}/ai-extract",
    response_model=schemas.AIGrantExtraction,
)
def ai_extract_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.require_admin),
):
    uploaded_document = (
        db.query(models.Document)
        .filter(models.Document.id == document_id)
        .first()
    )

    if not uploaded_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    file_path = Path(uploaded_document.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file not found",
        )

    try:
        extracted_text = extract_document_text(file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not extract text from document",
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text was found",
        )

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY is not configured",
        )

    try:
        client = OpenAI()

        response = client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Extract research grant information from the supplied "
                        "document text. Do not invent missing information. "
                        "Return null for fields that cannot be found. "
                        "Convert monetary amounts into plain numeric values. "
                        "Convert dates into YYYY-MM-DD format. "
                        "Keep the summary under 100 words."
                    ),
                },
                {
                    "role": "user",
                    "content": extracted_text[:50000],
                },
            ],
            text_format=schemas.AIGrantExtraction,
        )

        result = response.output_parsed

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The AI did not return structured grant data",
            )

        return result

    except HTTPException:
        raise
    except Exception as error:
        print(f"OpenAI extraction error: {error}")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI document extraction failed",
        )
    
@app.get("/reports/grants.csv")
def export_grants_csv(
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    grants = db.query(models.Grant).order_by(models.Grant.id).all()

    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)

    writer.writerow([
        "ID",
        "Title",
        "Principal Investigator",
        "Funding Agency",
        "Amount",
        "Deadline",
        "Status",
        "Compliance Status",
        "Created At",
        "Updated At",
    ])

    for grant in grants:
        writer.writerow([
            grant.id,
            grant.title,
            grant.principal_investigator,
            grant.funding_agency,
            grant.amount,
            grant.deadline,
            grant.status,
            grant.compliance_status or "",
            grant.created_at,
            grant.updated_at or "",
        ])

    csv_buffer.seek(0)

    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; filename="grant_report.csv"'
            )
        },
    )

@app.get("/reports/grants.xlsx")
def export_grants_excel(
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    grants = db.query(models.Grant).order_by(models.Grant.id).all()

    report_rows = [
        {
            "ID": grant.id,
            "Title": grant.title,
            "Principal Investigator": grant.principal_investigator,
            "Funding Agency": grant.funding_agency,
            "Amount": float(grant.amount),
            "Deadline": grant.deadline,
            "Status": grant.status,
            "Compliance Status": grant.compliance_status or "",
            "Created At": (
                grant.created_at.replace(tzinfo=None)
                if grant.created_at
                else None
            ),
            "Updated At": (
                grant.updated_at.replace(tzinfo=None)
                if grant.updated_at
                else None
            ),
        }
        for grant in grants
    ]

    spreadsheet = pd.DataFrame(report_rows)

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl",
    ) as writer:
        spreadsheet.to_excel(
            writer,
            index=False,
            sheet_name="Grants",
        )

    excel_buffer.seek(0)

    return StreamingResponse(
        excel_buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="grant_report.xlsx"'
            )
        },
    )

@app.get(
    "/audit-logs",
    response_model=List[schemas.AuditLogResponse],
)
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user=Depends(auth.require_admin),
):
    return crud.get_audit_logs(db)

@app.get(
    "/tasks",
    response_model=List[schemas.TaskResponse],
)
def list_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    return crud.get_tasks(db)


@app.put(
    "/tasks/{task_id}",
    response_model=schemas.TaskResponse,
)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(auth.require_admin),
):
    task = crud.update_task(
        db,
        task_id,
        task_update,
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    crud.create_audit_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        resource_type="Task",
        resource_id=task.id,
        details=f"Updated task: {task.title}",
    )

    return task