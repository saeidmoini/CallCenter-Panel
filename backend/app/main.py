from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.db import Base, engine
from .core.config import get_settings
from .api import (
    auth,
    admins,
    schedule,
    numbers,
    dialer,
    stats,
    billing,
    companies,
    scenarios,
    outbound_lines,
)

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Salehi Dialer Admin Panel - Multi-Company")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes (no company scope)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# Company management routes (superuser only)
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])

# Company-scoped routes (include {company_name} in path)
app.include_router(admins.router, prefix="/api", tags=["admins"])
app.include_router(schedule.router, prefix="/api", tags=["schedule"])
app.include_router(billing.router, prefix="/api", tags=["billing"])
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(outbound_lines.router, prefix="/api", tags=["outbound-lines"])

# Shared resources (numbers are global, dialer uses query params)
app.include_router(numbers.router, prefix="/api/numbers", tags=["numbers"])
app.include_router(dialer.router, prefix="/api/dialer", tags=["dialer"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])


@app.get("/health")
def health():
    return {"status": "ok"}
