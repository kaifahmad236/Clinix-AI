from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth_router, chat_router, report_router, dashboard_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ClinixAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(report_router.router)
app.include_router(dashboard_router.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "ClinixAI API"}
