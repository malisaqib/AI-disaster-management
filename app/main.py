from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import disasters, organizations, beneficiaries, programs, incidents, rag
from app.database import close_pool
from dotenv import load_dotenv
import os
import hmac

load_dotenv()

app = FastAPI(title="DisasterLink API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_KEY", "")

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if API_KEY:
        excluded = {"/", "/health", "/docs", "/openapi.json", "/redoc"}
        if request.url.path not in excluded:
            key = request.headers.get("X-API-Key")
            if not key or not hmac.compare_digest(key, API_KEY):
                return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    response = await call_next(request)
    return response

app.include_router(disasters.router)
app.include_router(organizations.router)
app.include_router(beneficiaries.router)
app.include_router(programs.router)
app.include_router(incidents.router)
app.include_router(rag.router)

@app.on_event("shutdown")
def shutdown_event():
    close_pool()

@app.get("/")
def root():
    return {"message": "DisasterLink API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
