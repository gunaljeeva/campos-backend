from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str
    supabase_jwt_secret: str
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
