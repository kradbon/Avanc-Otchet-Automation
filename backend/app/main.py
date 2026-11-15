from __future__ import annotations

from contextlib import asynccontextmanager
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, staff
from app.core.config import settings
from app.db.database import init_db, open_connection
from app.services.seed import seed_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with open_connection() as connection:
        seed_database(connection)
    yield


app = FastAPI(
    title="Avanc Otchet Automation API",
    description="Сервис производственных и авансовых отчетов для сотрудников и администраторов.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(staff.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Avanc Otchet Automation API",
        "status": "ok",
        "docs": "/docs",
    }
