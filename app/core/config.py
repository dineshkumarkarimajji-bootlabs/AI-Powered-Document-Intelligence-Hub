from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    UPLOAD_DIR: str
    CHROMA_DB_DIR: str
    EMBEDDING_MODEL: str
    OLLAMA_MODEL: str

    class Config:
        env_file = ".env"

settings = Settings()
