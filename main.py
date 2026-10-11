from fastapi import FastAPI
from app.routers import documents

app = FastAPI(title="Invoice AI")
app.include_router(documents.router)