from fastapi import FastAPI

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