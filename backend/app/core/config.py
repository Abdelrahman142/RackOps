from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "RackOps"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "postgresql://rackops_user:rackops_password"
        "@localhost:5432/rackops"
    )

    SECRET_KEY: str = "rackops-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
