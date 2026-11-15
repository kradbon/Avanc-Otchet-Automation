from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    base_dir: Path = Path(__file__).resolve().parents[2]
    api_prefix: str = "/api"
    secret_key: str = os.getenv("SECRET_KEY", "avanc-automation-secret-key")
    algorithm: str = "HS256"
    access_token_expire_hours: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "12"))
    frontend_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )

    @property
    def database_path(self) -> Path:
        custom_value = os.getenv("DATABASE_PATH")
        if custom_value:
            return Path(custom_value)
        return self.base_dir / "avanc.db"

    @property
    def pdf_storage_dir(self) -> Path:
        return self.base_dir / "storage" / "expense_reports"

    @property
    def production_pdf_storage_dir(self) -> Path:
        return self.base_dir / "storage" / "production_reports"


settings = Settings()
