"""
FastAPI application entry point.
Registers all routers, creates DB tables, configures CORS.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base
from backend.routers  import upload, analysis, chat, history

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title       = "EarningsIQ API",
    description = "Earnings call intelligence platform",
    version     = "1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"]
)

# Register routers
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(history.router)


@app.get("/")
async def root():
    return {"status": "EarningsIQ API running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}