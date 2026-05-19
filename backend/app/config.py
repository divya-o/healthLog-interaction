from pydantic_settings import BaseSettings, SettingsConfigDict
 

class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
 
    # LLM
    groq_api_key: str
    groq_primary_model: str = "gemma2-9b-it"
    groq_fallback_model: str = "llama-3.3-70b-versatile"
 
    # Database
    database_url: str
 
    # App
    app_env: str = "development"
    secret_key: str = "dev-secret"
    allowed_origins: str = "http://localhost:3000"
 
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]
 
 

settings = Settings()
 