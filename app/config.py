from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str
    supabase_jwt_secret: str
    jwt_secret: str = "change-me-local-dev-secret"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    # Email (Gmail SMTP by default). Leave user/password blank to disable sending.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""  # falls back to smtp_user
    app_base_url: str = "http://localhost:8080"  # used to build the login link in emails

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def emails_enabled(self) -> bool:
        return bool(self.smtp_user and self.smtp_password)

    @property
    def email_from(self) -> str:
        return self.smtp_from or self.smtp_user

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
