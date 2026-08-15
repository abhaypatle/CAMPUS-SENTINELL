from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.db.session import Base, engine
from src.models.user import User
from src.models.incident import IncidentReport
from src.auth.routes import router as auth_router
from src.reports.routes import router as reports_router
from src.models.incident_analysis import IncidentAnalysis
from src.reports.analysis_routes import router as analysis_router
from src.models.fusion import FusedIncident
from src.reports.fusion_routes import router as fusion_router
from src.reports.risk_routes import router as risk_router
from src.reports.escalation_routes import router as escalation_router
from src.reports.admin_routes import router as admin_router
from src.reports.recommendation_routes import router as recommendation_router
from src.reports.assignment_routes import router as assignment_router


app = FastAPI(
    title="Campus Sentinel API",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5180",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)


app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(analysis_router)
app.include_router(fusion_router)
app.include_router(risk_router)
app.include_router(escalation_router)
app.include_router(admin_router)
app.include_router(recommendation_router)
app.include_router(assignment_router)


@app.get("/")
def root():
    return {
        "message": "Campus Sentinel API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected",
        }

from src.reports.audit_routes import router as audit_router
app.include_router(audit_router)

from src.reports.realtime_routes import router as realtime_router
app.include_router(realtime_router)
