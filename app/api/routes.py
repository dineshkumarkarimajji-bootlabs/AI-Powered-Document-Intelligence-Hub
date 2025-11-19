from fastapi import APIRouter

from app.models.db import engine, Base

# --- Import all API modules ---
from app.api.utility.auth import router as auth_router
from app.api.utility.upload import router as upload_router
from app.api.utility.search import router as search_router
from app.api.utility.rag import router as rag_router
from app.api.utility.ocr import router as ocr_router
from app.api.utility.summarize import router as summarize_router    
from app.api.utility.format import router as format_router
from app.api.utility.user_docs import router as user_docs_router



# Create main API router
router = APIRouter()

# Attach all sub-routers
router.include_router(auth_router)
router.include_router(upload_router)
router.include_router(search_router)
router.include_router(rag_router)
router.include_router(ocr_router)
router.include_router(summarize_router)
router.include_router(format_router)
router.include_router(user_docs_router)

# Create tables
Base.metadata.create_all(bind=engine)
