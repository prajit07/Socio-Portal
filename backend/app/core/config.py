from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    DATABASE_URL: str = (
        "postgresql://placeholder:placeholder@ep-placeholder.region.aws.neon.tech/neondb?sslmode=require"
    )
    JWT_SECRET: str = "local-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173"

    # AI / LLM (pluggable). Leave CLOUDFLARE_* empty to use the built-in heuristic engine.
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_AI_API_KEY: str = ""
    CLOUDFLARE_AI_MODEL: str = "@cf/moonshotai/kimi-k2.7-code"
    DUPLICATE_THRESHOLD: float = 0.6

    # Email OTP (Google SMTP). Paste your sender address + app password below to
    # enable real email sending. When EMAIL_USER/EMAIL_PASS are empty, OTP codes are
    # printed to the server console (dev mode) so the flow is testable without creds.
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = ""  # sender Gmail address, e.g. you@gmail.com
    EMAIL_PASS: str = ""  # Gmail app password (NOT your normal password)
    EMAIL_FROM_NAME: str = "Socio Connect"
    OTP_TTL_SECONDS: int = 300
    OTP_LENGTH: int = 6
    EMAIL_VERIFICATION_REQUIRED: bool = False

    @property
    def ai_enabled(self) -> bool:
        return bool(self.CLOUDFLARE_ACCOUNT_ID and self.CLOUDFLARE_AI_API_KEY)

    @property
    def email_configured(self) -> bool:
        return bool(self.EMAIL_USER and self.EMAIL_PASS)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
