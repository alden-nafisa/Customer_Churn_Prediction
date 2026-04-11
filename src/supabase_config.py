from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class SupabaseConfig:
    project_url: str | None
    anon_key: str | None
    service_role_key: str | None
    db_host: str | None
    db_port: int
    db_name: str | None
    db_user: str | None
    db_password: str | None
    db_sslmode: str

    @property
    def database_url(self) -> str | None:
        if not all([self.db_host, self.db_name, self.db_user, self.db_password]):
            return None
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?sslmode={self.db_sslmode}"
        )

    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        if not self.project_url:
            missing.append("SUPABASE_URL")
        if not self.anon_key:
            missing.append("SUPABASE_ANON_KEY")
        if not self.db_host:
            missing.append("SUPABASE_DB_HOST")
        if not self.db_name:
            missing.append("SUPABASE_DB_NAME")
        if not self.db_user:
            missing.append("SUPABASE_DB_USER")
        if not self.db_password:
            missing.append("SUPABASE_DB_PASSWORD")
        return missing


def load_supabase_config() -> SupabaseConfig:
    return SupabaseConfig(
        project_url=getenv("SUPABASE_URL"),
        anon_key=getenv("SUPABASE_ANON_KEY"),
        service_role_key=getenv("SUPABASE_SERVICE_ROLE_KEY"),
        db_host=getenv("SUPABASE_DB_HOST"),
        db_port=int(getenv("SUPABASE_DB_PORT", "5432")),
        db_name=getenv("SUPABASE_DB_NAME", "postgres"),
        db_user=getenv("SUPABASE_DB_USER", "postgres"),
        db_password=getenv("SUPABASE_DB_PASSWORD"),
        db_sslmode=getenv("SUPABASE_DB_SSLMODE", "require"),
    )